from typing import TYPE_CHECKING, TypedDict, Dict, NotRequired, List, Tuple

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataline.models.base import DBModel, UUIDMixin
from dataline.models.connection.schema import ConnectionConfigSchema

if TYPE_CHECKING:
    from dataline.models.conversation.model import ConversationModel


class ConnectionSchemaTableColumnRelationship(TypedDict):
    schema_name: str
    table: str
    column: str
    enabled: bool


class ConnectionSchemaTableColumn(TypedDict):
    name: str
    possible_values: list[str]
    primary_key: bool
    description: str
    relationship: list[ConnectionSchemaTableColumnRelationship]
    enabled: bool


class ConnectionSchemaTable(TypedDict):
    name: str
    enabled: bool
    columns: list[ConnectionSchemaTableColumn]
    description: str

class ConnectionConfig(TypedDict):
    validation_query: NotRequired[str]
    connection_prompt: NotRequired[str]
    default_table_limit: NotRequired[int]

class ConnectionSchema(TypedDict):
    name: str
    tables: list[ConnectionSchemaTable]
    enabled: bool


class ConnectionOptions(TypedDict):
    schemas: list[ConnectionSchema]


class ConnectionModel(DBModel, UUIDMixin, kw_only=True):
    __tablename__ = "connections"
    dsn: Mapped[str] = mapped_column("dsn", String, nullable=False, unique=True)
    database: Mapped[str] = mapped_column("database", String, nullable=False)
    name: Mapped[str | None] = mapped_column("name", String)
    type: Mapped[str] = mapped_column("type", String, nullable=False)
    dialect: Mapped[str | None] = mapped_column("dialect", String)
    is_sample: Mapped[bool] = mapped_column("is_sample", Boolean, nullable=False, default=False, server_default="false")
    glossary: Mapped[Dict[str, str] | None] = mapped_column("glossary", JSON, nullable=True)
    options: Mapped[ConnectionOptions | None] = mapped_column("options", JSON, nullable=True)
    unique_value_dict: Mapped[Dict[str, List[Tuple[str,str]]] | None ] = mapped_column("unique_value_dict", JSON, nullable=True)
    config: Mapped[ConnectionConfigSchema | None] = mapped_column('config', JSON, nullable=True)

    # Relationships
    conversations: Mapped[list["ConversationModel"]] = relationship("ConversationModel", back_populates="connection")
