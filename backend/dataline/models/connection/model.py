from typing import TYPE_CHECKING, TypedDict

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataline.models.base import DBModel, UUIDMixin

if TYPE_CHECKING:
    from dataline.models.conversation.model import ConversationModel


class ConnectionSchemaTableColumnRelationship(TypedDict):
    schema: str
    table: str
    column: str


class ConnectionSchemaTableColumn(TypedDict):
    name: str
    possible_values: list[str]
    primary_key: bool
    description: str
    relationship: list[ConnectionSchemaTableColumnRelationship]


class ConnectionSchemaTable(TypedDict):
    name: str
    enabled: bool
    columns: list[ConnectionSchemaTableColumn]
    description: str


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
    options: Mapped[ConnectionOptions | None] = mapped_column("options", JSON, nullable=True)

    # Relationships
    conversations: Mapped[list["ConversationModel"]] = relationship("ConversationModel", back_populates="connection")
