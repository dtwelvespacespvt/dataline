from typing import Sequence, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from dataline.models.conversation.model import ConversationModel
from dataline.models.llm_flow.enums import QueryResultType
from dataline.models.message.model import MessageModel
from dataline.models.message.schema import MessageCreate, MessageUpdate
from dataline.models.result.model import ResultModel
from dataline.repositories.base import AsyncSession, BaseRepository


class MessageRepository(BaseRepository[MessageModel, MessageCreate, MessageUpdate]):
    @property
    def model(self) -> Type[MessageModel]:
        return MessageModel

    async def get_by_conversation(self, session: AsyncSession, conversation_id: UUID) -> Sequence[MessageModel]:
        query = select(MessageModel).filter_by(conversation_id=conversation_id).order_by(MessageModel.created_at)
        return await self.list(session, query=query)

    async def get_by_conversation_with_sql_results(
        self, session: AsyncSession, conversation_id: UUID, n: int = 10
    ) -> Sequence[MessageModel]:
        query = (
            select(MessageModel)
            .filter_by(conversation_id=conversation_id)
            .outerjoin(
                ResultModel,
                onclause=(ResultModel.message_id == MessageModel.id)
                & (ResultModel.type == QueryResultType.SQL_QUERY_STRING_RESULT.value),
            )
            .options(contains_eager(MessageModel.results))
            .order_by(MessageModel.created_at.desc())
            .limit(n)
        )
        return await self.list_unique(session, query=query)

    async def get_by_connection_and_user_with_sql_results(self, session: AsyncSession, connection_id: UUID, user_id:UUID, n: int = 10) -> Sequence[MessageModel]:
        query = (
            select(MessageModel)
            .join(ConversationModel)
            .where(
        ConversationModel.connection_id == connection_id,
                    ConversationModel.user_id == user_id
            ).limit(n)
            # .outerjoin(
            #     ResultModel,
            #     onclause=(ResultModel.message_id == MessageModel.id)
            #     & (ResultModel.type == QueryResultType.SQL_QUERY_STRING_RESULT.value),
            # )
            # .options(contains_eager(MessageModel.results))
            .order_by(MessageModel.created_at.desc())
            # .limit(n)
        )
        return await self.list_unique(session, query=query)