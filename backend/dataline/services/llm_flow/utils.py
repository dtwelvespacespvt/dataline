from collections import defaultdict
from typing import Any, Generator, Protocol, Self, Sequence, cast

import logging
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import Engine, MetaData, Row, create_engine, inspect
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import CreateTable
from sqlalchemy.engine import make_url
from sqlalchemy import text

from dataline.models.connection.model import ConnectionSchemaTableColumn
from dataline.models.connection.schema import ConnectionOptions, ConnectionConfigSchema
import json

logger = logging.getLogger(__name__)


class ConnectionProtocol(Protocol):
    dsn: str
    options: ConnectionOptions | None
    config: ConnectionConfigSchema | None


class DatalineSQLDatabase(SQLDatabase):
    """SQLAlchemy wrapper around a database."""

    def __init__(
        self,
        engine: Engine,
        schemas: list[str] | None = None,
        metadata: MetaData | None = None,
        ignore_tables: list[str] | None = None,
        include_tables: list[str] | None = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: dict | None = None,
        view_support: bool = True,
        max_string_length: int = 300,
        table_prefixes: list[str] | None = None,
        blacklisted_table_suffixes: list[str] | None = None,
        inspect_allowed: bool = True,
    ):
        """Create engine from database URI."""
        self._engine = engine
        self._schema = None  # need to keep this as it is used inside super()._execute method
        if schemas is None:
            inspector = inspect(self._engine)
            self._schemas = inspector.get_schema_names()
        else:
            self._schemas = schemas
        if include_tables and ignore_tables:
            raise ValueError("Cannot specify both include_tables and ignore_tables")

        self._inspector = inspect(self._engine)
        # including view support by adding the views as well as tables to the all
        # tables list if view_support is True
        self._all_tables_per_schema: dict[str, set[str]] = {}
        for schema in self._schemas:
            all_table_like_names = self._inspector.get_table_names(schema=schema)
            if view_support:
                all_table_like_names += self._inspector.get_view_names(schema=schema)
            filtered_table_names = set()
            for name in all_table_like_names:
                # Filter by prefix
                if table_prefixes and not any(name.startswith(prefix) for prefix in table_prefixes):
                    continue
                # Filter by suffix
                if blacklisted_table_suffixes and any(name.endswith(suffix) for suffix in blacklisted_table_suffixes):
                    continue
                filtered_table_names.add(name)
            self._all_tables_per_schema[schema] = filtered_table_names

        self._all_tables = set(f"{k}.{name}" for k, names in self._all_tables_per_schema.items() for name in names)

        self._include_tables = set(include_tables) if include_tables else set()
        if self._include_tables:
            missing_tables = self._include_tables - self._all_tables
            if missing_tables:
                raise ValueError(f"include_tables {missing_tables} not found in database")
        self._ignore_tables = set(ignore_tables) if ignore_tables else set()
        if self._ignore_tables:
            missing_tables = self._ignore_tables - self._all_tables
            if missing_tables:
                raise ValueError(f"ignore_tables {missing_tables} not found in database")
        usable_tables = self.get_usable_table_names()
        self._usable_tables = set(usable_tables) if usable_tables else self._all_tables

        if not isinstance(sample_rows_in_table_info, int):
            raise TypeError("sample_rows_in_table_info must be an integer")

        self._sample_rows_in_table_info = sample_rows_in_table_info
        self._indexes_in_table_info = indexes_in_table_info

        self._custom_table_info = custom_table_info
        if self._custom_table_info:
            if not isinstance(self._custom_table_info, dict):
                raise TypeError(
                    "table_info must be a dictionary with table names as keys and the " "desired table info as values"
                )
            # only keep the tables that are also present in the database
            intersection = set(self._custom_table_info).intersection(self._all_tables)
            self._custom_table_info = dict(
                (table, self._custom_table_info[table]) for table in self._custom_table_info if table in intersection
            )

        self._max_string_length = max_string_length

        self._metadata = metadata or MetaData()
        # including view support if view_support = true
        if inspect_allowed:
            for schema in self._schemas:
                self._metadata.reflect(
                    views=view_support,
                    bind=self._engine,
                    only=[table.split(".")[-1] for table in self._usable_tables if table.startswith(f"{schema}.")],
                    schema=schema,
                )

        # # Add id to tables metadata
        # for t in self._metadata.sorted_tables:
        #     t.id = f"{t.schema}.{t.name}"

    # def from_uri(cls, database_uri: str | URL, engine_args: dict | None = None, **kwargs: Any) -> Self:
    @classmethod
    def from_uri(
        cls, database_uri: str, schemas: list[str] | None = None,
            engine_args: dict | None = None, **kwargs: Any
    ) -> Self:
        """Construct a SQLAlchemy engine from URI."""
        url = make_url(database_uri)
        query = url.query
        view_support = query.get("view_support", "true").lower() == "true"
        inspect_allowed = query.get("inspect", "true").lower() == "true"
        if schemas is None or len(schemas) == 0:
            str_schemas = query.get("schemas")
            schemas = [s.strip() for s in str_schemas.split(",")] if str_schemas else None
        ignore_tables = query.get("ignore_tables")
        table_prefixes = query.get("table_prefixes")
        blacklisted_table_suffixes = query.get("blacklisted_table_suffixes")
        parsed_ignore_tables = [t.strip() for t in ignore_tables.split(",")] if ignore_tables else []
        include_tables = kwargs.pop("include_tables", None)
        custom_table_info = kwargs.pop("custom_table_info", None)
        if include_tables is None:
            str_include_tables = query.get("include_tables")
            parsed_include_tables = [t.strip() for t in str_include_tables.split(",")] if str_include_tables else []
        else:
            parsed_include_tables = include_tables
        parsed_table_prefixes = [t.strip() for t in table_prefixes.split(",")] if table_prefixes else []
        parsed_blacklisted_table_suffixes = [t.strip() for t in blacklisted_table_suffixes.split(",")] \
            if blacklisted_table_suffixes else []
        _engine_args = engine_args or {}
        new_database_uri = url.set(query={})
        uri_with_password = str(new_database_uri.render_as_string(hide_password=False))
        engine = create_engine(uri_with_password, **_engine_args)
        return cls(engine,
                   schemas=schemas,
                   view_support=view_support,
                   ignore_tables=parsed_ignore_tables,
                   include_tables=parsed_include_tables,
                   custom_table_info=custom_table_info,
                   table_prefixes=parsed_table_prefixes,
                   blacklisted_table_suffixes=parsed_blacklisted_table_suffixes,
                   inspect_allowed=inspect_allowed,
                   **kwargs)

    def custom_run_sql_stream(self, query: str) -> Generator[Sequence[Row[Any]], Any, None]:
        # https://docs.sqlalchemy.org/en/20/core/connections.html#streaming-with-a-fixed-buffer-via-yield-per
        yield_per = 1000
        if self.dialect == "mssql":
            with self._engine.begin() as connection:
                command = text(query)
                with connection.execution_options(yield_per=yield_per).execute(command) as result:
                    columns = list(result.keys())
                    yield columns
                    for partition in result.partitions():
                        for row in partition:
                            yield row

        result = cast(
            CursorResult[Any],
            super().run(query, "cursor", include_columns=True, execution_options={"yield_per": yield_per}),
        )  # type: ignore[misc]
        columns = list(result.keys())
        yield columns
        for partition in result.partitions():
            for row in partition:
                yield row

    def custom_run_sql(self, query: str) -> tuple[list[Any], Sequence[Row[Any]]]:
        if self.dialect == "mssql":
            with self._engine.begin() as connection:
                command = text(query)
                result = connection.execute(command)
                rows = result.fetchall()
                columns = list(result.keys())
                return columns, rows

        result = cast(CursorResult[Any], super().run(query, "cursor", include_columns=True))  # type: ignore[misc]
        rows = result.fetchall()
        columns = list(result.keys())
        return columns, rows

    @classmethod
    def from_dataline_connection(
        cls, connection: ConnectionProtocol, engine_args: dict | None = None, **kwargs: Any
    ) -> Self:
        """Construct a SQLAlchemy engine from Dataline connection."""
        if connection.options:
            enabled_schemas = [schema for schema in connection.options.schemas if schema.enabled]
            schemas_str = [schema.name for schema in enabled_schemas]
            include_tables = [
                f"{schema.name}.{table.name}" for schema in enabled_schemas for table in schema.tables if table.enabled
            ]
            custom_table_info = {
                f"{schema.name}.{table.name}": {
                    "name": table.name,
                    "description": table.description,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "primary_key": col.primary_key,
                            "possible_values": col.possible_values,
                            "description": col.description,
                            "relationship": [
                                {
                                    "schema_name": relationship.schema_name,
                                    "table": relationship.table,
                                    "column": relationship.column
                                }
                                for relationship in col.relationship
                                if relationship.enabled
                            ]
                        }
                        for col in table.columns
                        if col.enabled
                    ]
                }
                for schema in enabled_schemas
                for table in schema.tables
                if table.enabled
            }
        else:
            schemas_str = None
            include_tables = None
            custom_table_info = None
        return cls.from_uri(
            database_uri=connection.dsn,
            schemas=schemas_str,
            engine_args=engine_args,
            include_tables=include_tables,
            custom_table_info=custom_table_info,
            **kwargs,
        )

    def get_column_info_per_table_per_schema(self, schema: str | None = None, table: str | None = None) -> list:
        columns = []
        column_meta = []
        primary_keys = []
        try:
            if self._engine.dialect.name == "redshift":
                query = text("""
                    SELECT column_name as name, data_type as type
                    FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                    """)
                with self._engine.connect() as conn:
                    result = conn.execute(query, {"schema": schema, "table": table}).fetchall()
                    columns = [dict(row._mapping) for row in result]
            else:
                columns = self._inspector.get_columns(table, schema=schema)
        except NoSuchTableError as e:
            logger.info(table)
        if len(columns) > 0 and self._engine.dialect.name != "redshift":
            try:
                primary_keys = self._inspector.get_pk_constraint(table).get("constrained_columns", [])
            except NoSuchTableError as e:
                logger.info(f"primary key not available in {table}")
        for column in columns:
            column_meta.append({
                "name": column["name"],
                "type": str(column["type"]),
                "primary_key": column["name"] in primary_keys
            })
        return column_meta

    def get_table_info(self, table_names: list[str] | None = None) -> str:
        """Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_table_info`, the specified number of sample rows will be
        appended to each table description. This can increase performance as
        demonstrated in the paper.
        """
        all_table_names = self.get_usable_table_names()
        if table_names is not None:
            missing_tables = set(table_names).difference(all_table_names)
            if missing_tables:
                raise ValueError(f"table_names {missing_tables} not found in database")
            all_table_names = table_names

        meta_tables = [
            tbl
            for tbl in self._metadata.sorted_tables
            if f"{tbl.schema}.{tbl.name}" in set(all_table_names)
            and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
        ]
        tables = []
        if len(meta_tables) > 0:
            for table in meta_tables:
                if self._custom_table_info and f"{table.schema}.{table.name}" in self._custom_table_info:
                    tables.append(json.dumps(self._custom_table_info[f"{table.schema}.{table.name}"]))

                # add create table command
                create_table = str(CreateTable(table).compile(self._engine))
                table_info = f"{create_table.rstrip()}"
                has_extra_info = self._indexes_in_table_info or self._sample_rows_in_table_info
                if has_extra_info:
                    table_info += "\n\n/*"
                if self._indexes_in_table_info:
                    table_info += f"\n{self._get_table_indexes(table)}\n"
                if self._sample_rows_in_table_info:
                    table_info += f"\n{self._get_sample_rows(table)}\n"
                if has_extra_info:
                    table_info += "*/"
                tables.append(table_info)
        else:
            for table in set(all_table_names):
                if self._custom_table_info and table in self._custom_table_info:
                    tables.append(json.dumps(self._custom_table_info[table]))
        final_str = "\n\n".join(tables)
        logger.debug(f"get_table_info {final_str}")
        return final_str


    def generate_unique_values_sql(self, table_to_columns:tuple[str,list[ConnectionSchemaTableColumn]], schema_name:str|None=None):
        sql_parts = []
        unique_value_dict = defaultdict(list)

        if not table_to_columns[1]:
            return unique_value_dict

        table_name = table_to_columns[0]

        for col in table_to_columns[1]:
            col_name= col.name
            subquery = (
                f"SELECT '{table_name}' AS TableName, "
                f"'{col_name}' AS ColumnName, "
                f"{col_name} AS UniqueValue "
                f"FROM {schema_name}.{table_name} "
                f"GROUP BY {col_name}"
            )
            sql_parts.append(subquery)

        query = text(" UNION ALL ".join(sql_parts) + ";")
        columns = []
        with self._engine.connect() as conn:
            result = conn.execute(query, {"schema": schema_name, "table": table_name}).fetchall()
            columns = [dict(row._mapping) for row in result]

        for column in columns:
            key = column['uniquevalue']
            value_tuple = (column['columnname'], column['tablename'])
            unique_value_dict[key].append(value_tuple)


        return unique_value_dict
