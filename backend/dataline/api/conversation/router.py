import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dataline.auth import UserInfo, security
from dataline.models.conversation.schema import (
    ConversationOut,
    ConversationWithMessagesWithResultsOut,
    CreateConversationIn,
    UpdateConversationRequest,
)
from dataline.models.llm_flow.schema import SQLQueryRunResult
from dataline.models.message.schema import MessageOptions, MessageWithResultsOut, MessageFeedBack
from dataline.models.result.schema import ResultOut
from dataline.old_models import SuccessListResponse, SuccessResponse
from dataline.repositories.base import AsyncSession, get_session
from dataline.services.connection import ConnectionService
from dataline.services.conversation import ConversationService
from dataline.services.llm_flow.toolkit import execute_sql_query
from dataline.services.llm_flow.utils import DatalineSQLDatabase as SQLDatabase
from dataline.utils.posthog import posthog_capture
from dataline.utils.utils import generate_with_errors

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])

class QueryRequest(BaseModel):
    query: str
    message_options: MessageOptions

@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
    conversation_service: ConversationService = Depends(),
) -> SuccessResponse[ConversationOut]:
    conversation = await conversation_service.get_conversation(session, conversation_id=conversation_id)
    return SuccessResponse(data=conversation)


@router.get("/conversations")
async def conversations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_session),
    conversation_service: ConversationService = Depends()
) -> SuccessListResponse[ConversationWithMessagesWithResultsOut]:
    return SuccessListResponse(
        data= await conversation_service.get_conversations(session, skip, limit),
    )


@router.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    conversation_service: Annotated[ConversationService, Depends()],
    background_tasks: BackgroundTasks,
    user_info: UserInfo = Depends(security)
) -> SuccessListResponse[MessageWithResultsOut]:
    background_tasks.add_task(posthog_capture, "conversation_opened")
    conversation = await conversation_service.get_conversation_with_messages(session, conversation_id=conversation_id)
    messages = [MessageWithResultsOut.model_validate(message) for message in conversation.messages]
    return SuccessListResponse(data=messages)


@router.post("/conversation")
async def create_conversation(
    conversation_in: CreateConversationIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    conversation_service: Annotated[ConversationService, Depends()],
    background_tasks: BackgroundTasks
) -> SuccessResponse[ConversationOut]:
    background_tasks.add_task(posthog_capture, "conversation_created")
    conversation = await conversation_service.create_conversation(
        session, connection_id=conversation_in.connection_id, name=conversation_in.name
    )
    return SuccessResponse(
        data=conversation,
    )


@router.patch("/conversation/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    conversation_in: UpdateConversationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    conversation_service: Annotated[ConversationService, Depends()],
) -> SuccessResponse[ConversationOut]:
    conversation = await conversation_service.update_conversation_name(
        session, conversation_id=conversation_id, name=conversation_in.name
    )
    return SuccessResponse(data=conversation)


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    conversation_service: Annotated[ConversationService, Depends()],
) -> None:
    return await conversation_service.delete_conversation(session, conversation_id)


@router.post("/conversation/{conversation_id}/query")
def query(
    conversation_id: UUID,
    request_body: QueryRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    conversation_service: Annotated[ConversationService, Depends()],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        posthog_capture,
        "message_sent",
        {"conversation_id": str(conversation_id), "is_secure": request_body.message_options.secure_data},
    )
    response_generator = conversation_service.query(
        session, conversation_id, request_body.query, secure_data=request_body.message_options.secure_data, debug=request_body.message_options.debug, background_tasks = background_tasks)
    return StreamingResponse(
        generate_with_errors(response_generator),
        media_type="text/event-stream",
    )


@router.get("/conversation/{conversation_id}/run-sql")
async def execute_sql(
    conversation_id: UUID,
    sql: str,
    linked_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    conversation_service: Annotated[ConversationService, Depends()],
    connection_service: Annotated[ConnectionService, Depends()],
    background_tasks: BackgroundTasks,
    limit: int = 10,
    execute: bool = True,
) -> SuccessResponse[ResultOut]:
    background_tasks.add_task(posthog_capture, "sql_executed", {"conversation_id": str(conversation_id)})

    # Get conversation
    # Will raise error that's auto captured by middleware if not exists
    conversation = await conversation_service.get_conversation(session, conversation_id=conversation_id)

    # Get connection
    connection_id = conversation.connection_id
    connection = await connection_service.get_connection(session, connection_id)

    # Refresh chart data
    db = SQLDatabase.from_dataline_connection(connection)
    query_run_data = execute_sql_query(db, sql)

    # Execute query
    result = SQLQueryRunResult(
        columns=query_run_data.columns,
        rows=query_run_data.rows,
        for_chart=False,
        linked_id=linked_id,
    )

    return SuccessResponse(data=result.serialize_result())


@router.post("/conversation/{conversation_id}/generate-title")
async def generate_conversation_title(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
    conversation_service: ConversationService = Depends(),
) -> SuccessResponse[str]:
    title = await conversation_service.generate_title(session, conversation_id)
    return SuccessResponse(data=title)

@router.patch('/conversation/message/feedback')
async def update_message_feedback(message_feedback: MessageFeedBack,
    session: AsyncSession = Depends(get_session),
    conversation_service: ConversationService = Depends()) -> None:
    return await conversation_service.update_feedback(session, message_feedback)