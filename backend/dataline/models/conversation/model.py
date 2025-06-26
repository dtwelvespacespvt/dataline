from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from dataline.models.base import DBModel, UUIDMixin
from dataline.models.connection.model import ConnectionModel
from sqlalchemy import ForeignKey, String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from dataline.models.message.model import MessageModel


class ConversationModel(DBModel, UUIDMixin, kw_only=True):
    __tablename__ = "conversations"
    connection_id: Mapped[UUID] = mapped_column(ForeignKey(ConnectionModel.id, ondelete="CASCADE"))
    name: Mapped[str] = mapped_column("name", String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    messages: Mapped[list["MessageModel"]] = relationship("MessageModel", back_populates="conversation")
    connection: Mapped["ConnectionModel"] = relationship("ConnectionModel", back_populates="conversations")
