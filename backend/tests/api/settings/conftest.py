from unittest.mock import MagicMock, patch

import pytest_asyncio
from fastapi.testclient import TestClient

from openai.resources.models import Models as OpenAIModels



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
