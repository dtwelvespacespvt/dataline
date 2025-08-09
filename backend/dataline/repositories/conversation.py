from datetime import datetime
from typing import Sequence, Type, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from dataline.models.conversation.model import ConversationModel
from dataline.models.message.model import MessageModel
from dataline.repositories.base import AsyncSession, BaseRepository


class ConversationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    connection_id: UUID
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[UUID] = None


class ConversationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    connection_id: UUID | None = None
    name: str | None = None


class ConversationRepository(BaseRepository[ConversationModel, ConversationCreate, ConversationUpdate]):
    @property
    def model(self) -> Type[ConversationModel]:
        return ConversationModel

    async def get_with_messages_with_results(self, session: AsyncSession, conversation_id: UUID) -> ConversationModel:
        query = (
            select(ConversationModel)
            .filter_by(id=conversation_id)
            .options(joinedload(ConversationModel.messages).joinedload(MessageModel.results))
        )
        return await self.get_unique(session, query)

    async def list_with_messages_with_results_user(self, session: AsyncSession, user_id: UUID, skip:int=0, limit:int = None) -> Sequence[ConversationModel]:
        if limit:
            query = select(ConversationModel).options(
                joinedload(ConversationModel.messages).joinedload(MessageModel.results)
            ).where(ConversationModel.user_id == user_id).offset(skip).limit(limit)

        else:
            query = select(ConversationModel).options(
            joinedload(ConversationModel.messages).joinedload(MessageModel.results)
        ).where(ConversationModel.user_id == user_id )
        return await self.list_unique(session, query)

    async def list_with_messages_with_results(self, session: AsyncSession, skip:int=0, limit:int = None) -> Sequence[ConversationModel]:
        if limit:
            query = select(ConversationModel).options(
                joinedload(ConversationModel.messages).joinedload(MessageModel.results)
            ).offset(skip).limit(limit)
        else:
            query = select(ConversationModel).options(
            joinedload(ConversationModel.messages).joinedload(MessageModel.results)
        )
        return await self.list_unique(session, query)

