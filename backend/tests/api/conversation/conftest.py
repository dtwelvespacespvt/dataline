from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from dataline.models.connection.schema import Connection
from dataline.models.conversation.schema import ConversationOut
from dataline.repositories.base import AsyncSession
from openai.resources.models import Models as OpenAIModels


@pytest_asyncio.fixture
@pytest.mark.usefixtures("user_info")
async def sample_conversation(
    client: TestClient, session: AsyncSession, dvdrental_connection: Connection
) -> ConversationOut:
    data = {
        "connection_id": str(dvdrental_connection.id),
        "name": "Test convo",
    }
    response = client.post("/conversation", json=data)
    assert response.status_code == 200

    return ConversationOut(**response.json()["data"])

@pytest_asyncio.fixture
@patch.object(OpenAIModels, "list")
async def user_info(mock_openai_model_list: MagicMock, client: TestClient) -> dict[str, str]:
    mock_model = MagicMock()
    mock_model.id = "gpt-4.1-mini"
    mock_openai_model_list.return_value = [mock_model]
    user_in = {
        "name": "John",
        "openai_api_key": "sk-asoiasdfl",
    }
    client.patch("/settings/info", json=user_in)
    return user_in
