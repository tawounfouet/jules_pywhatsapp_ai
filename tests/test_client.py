import pytest
import respx
from httpx import Response

from whatsapp_ai.client import WhatsAppClient
from whatsapp_ai.config import WhatsAppConfig
from whatsapp_ai.exceptions import WhatsAppAPIError

@pytest.fixture
def config():
    return WhatsAppConfig(
        whatsapp_access_token="fake_token",
        whatsapp_phone_number_id="123456789",
        whatsapp_verify_token="verify_me",
        whatsapp_api_version="v18.0",
        openai_api_key="sk-fake",
    )

@pytest.fixture
def client(config):
    return WhatsAppClient(config)

@pytest.mark.asyncio
@respx.mock
async def test_send_text_message_success(client):
    url = "https://graph.facebook.com/v18.0/123456789/messages"

    # Mock the Meta API response
    respx.post(url).mock(return_value=Response(200, json={"messages": [{"id": "wamid.123"}]}))

    response = await client.send_text_message(to="33612345678", text="Hello")

    assert response["messages"][0]["id"] == "wamid.123"

@pytest.mark.asyncio
@respx.mock
async def test_send_text_message_failure(client):
    url = "https://graph.facebook.com/v18.0/123456789/messages"

    # Mock a failure
    respx.post(url).mock(return_value=Response(400, json={"error": "Bad request"}))

    with pytest.raises(WhatsAppAPIError) as exc_info:
        await client.send_text_message(to="33612345678", text="Hello")

    assert exc_info.value.status_code == 400
    assert "Bad request" in str(exc_info.value)
