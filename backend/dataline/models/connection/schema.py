import re
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dataline.config import config


class ConnectionSchemaTableColumnRelationship(BaseModel):
    schema_name: Optional[str] = None
    table: Optional[str] = None
    column: Optional[str] = None
    enabled: Optional[bool] = False


class ConnectionSchemaTableColumn(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    possible_values: Optional[list[str]] = []
    primary_key: Optional[bool] = False
    description: Optional[str] = None
    relationship: Optional[list[ConnectionSchemaTableColumnRelationship]] = []
    enabled: Optional[bool] = False
    reverse_look_up: Optional[bool] = False


class ConnectionSchemaTable(BaseModel):
    name: str
    enabled: bool
    columns: Optional[list[ConnectionSchemaTableColumn]] = []
    description: Optional[str] = None


class ConnectionSchema(BaseModel):
    name: str
    tables: list[ConnectionSchemaTable]
    enabled: bool


class ConnectionOptions(BaseModel):
    schemas: list[ConnectionSchema]

class ConnectionConfigSchema(BaseModel):
    validation_query: Optional[str] = None
    connection_prompt: Optional[str] = None
    default_table_limit: Optional[int] = None


class Connection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    dsn: str
    database: str
    dialect: str
    type: str
    is_sample: bool
    options: Optional[ConnectionOptions] = None
    glossary: Optional[Dict[str,Any]] = []
    unique_value_dict: Optional[dict[str,list[tuple[str,str]]]] = []
    config: Optional[ConnectionConfigSchema] = None


class ConnectionOut(Connection):
    model_config = ConfigDict(from_attributes=True)


class ConnectionIn(BaseModel):
    dsn: str = Field(min_length=3)
    name: str

    @field_validator("dsn")
    def validate_dsn_format(cls, value: str) -> str:
        # Define a regular expression to match the DSN format
        dsn_regex = r"^[\w\+]+:\/\/[\w-]+:\w+@[\w.-]+[:\d]*\/\w+$"

        if not re.match(dsn_regex, value):
            raise ValueError(
                'Invalid DSN format. The expected format is "driver://username:password@host:port/database".'
            )

        return value


class GetConnectionOut(BaseModel):
    connection: ConnectionOut


class GetConnectionListOut(BaseModel):
    connections: list[ConnectionOut]


class TableSchemaField(BaseModel):
    id: str
    schema_id: str
    name: str
    type: str
    description: str
    is_primary_key: Optional[bool]
    is_foreign_key: Optional[bool]
    linked_table: Optional[str]


class TableSchema(BaseModel):
    id: str
    connection_id: str
    name: str
    description: str
    field_descriptions: list[TableSchemaField]


class TableSchemasOut(BaseModel):
    tables: list[TableSchema]


class SampleOut(BaseModel):
    key: str
    title: str
    file: str
    link: str


class RelationshipOut(BaseModel):
    schema_name: str
    table: str
    column: str
    enabled: bool


def validate_dsn(value: str) -> str:
    # Regular expression pattern for matching DSNs
    # Try sqlite first
    sqlite_pattern = r"^sqlite://(/.+?)(:(.+))?$"
    if re.match(sqlite_pattern, value):
        return value

    dsn_pattern = (
        r"^(?P<db>[\w]+)(?P<driver>\+[\w]+)?:\/\/(?:(?P<username>\S+):(?P<password>\S+)@)?(?P<host>[\w\.-]+)"
        r"(?::(?P<port>\d+))?(?:\/(?P<database>[\w\.\/-]+))?(?:\?(?P<parameters>.*))?$"
    )
    match = re.match(dsn_pattern, value)
    if match:
        # Extracting components from the DSN
        db = match.group("db")
        driver = match.group("driver")
        host = match.group("host")
        database = match.group("database")

        # Validating components (You can customize the validation rules as per your requirements)
        if not db:
            raise ValueError("Missing database in DSN (ex. postgres://...)")

        if not host:
            raise ValueError("Host missing from DSN (ex. ...@localhost/db_name)")

        if not database:
            raise ValueError("DSN must specify a database name (ex .../dvd_rental)")

        if driver:
            # Remove user-supplied drivers, we will enforce our own
            value = value.replace(driver, "")
    else:
        # DSN doesn't match the expected pattern
        raise ValueError("Invalid DSN format")

    # Simpler way to connect to postgres even though officially deprecated
    # This mirrors psql which is a very common way to connect to postgres
    # Only replace first occurrence
    if value.startswith("postgres") and not value.startswith("postgresql"):
        value = value.replace("postgres", "postgresql", 1)
    elif value.startswith("mysql"):
        value = value.replace("mysql", "mysql+pymysql", 1)
    elif value.startswith("mssql"):
        value = value.replace("mssql", "mssql+pyodbc", 1)
    elif value.startswith("redshift"):
        value = value.replace("redshift", "redshift+redshift_connector", 1)

    return value


class ConnectRequest(BaseModel):
    dsn: str = Field(min_length=3)
    name: str
    is_sample: bool = False

    @field_validator("dsn")
    def validate_dsn_format(cls, value: str) -> str:
        return validate_dsn(value)


class ConnectionUpdateIn(BaseModel):
    name: Optional[str] = None
    dsn: Optional[str] = None
    options: Optional[ConnectionOptions] = None
    glossary: Dict[str,str] = None
    config: ConnectionConfigSchema = None
    unique_value_dict: Dict[str, list[tuple[str,str]]] = None

    @field_validator("dsn")
    def validate_dsn_format(cls, value: str) -> str:
        return validate_dsn(value)


class FileConnectionType(Enum):
    sqlite = "sqlite"
    csv = "csv"
    sas7bdat = "sas7bdat"
    excel = "excel"


class SampleName(Enum):
    dvdrental = "dvdrental"
    netflix = "netflix"
    titanic = "titanic"
    spotify = "spotify"


class ConnectSampleIn(BaseModel):
    sample_name: SampleName
    connection_name: str


DB_SAMPLES = {
    "dvdrental": (
        "Dvd Rental",
        config.sample_dvdrental_path,
        "https://www.postgresqltutorial.com/postgresql-getting-started/postgresql-sample-database/",
    ),
    "netflix": ("Netflix Shows", config.sample_netflix_path, "https://www.kaggle.com/datasets/shivamb/netflix-shows"),
    "titanic": (
        "Titanic",
        config.sample_titanic_path,
        "https://www.kaggle.com/datasets/ibrahimelsayed182/titanic-dataset",
    ),
    "spotify": (
        "Spotify",
        config.sample_spotify_path,
        "https://www.kaggle.com/datasets/ambaliyagati/spotify-dataset-for-playing-around-with-sql",
    ),
}
