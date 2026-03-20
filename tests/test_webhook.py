import pytest
from fastapi.testclient import TestClient

from whatsapp_ai.router import MessageRouter
from whatsapp_ai.webhook import WebhookReceiver

from whatsapp_ai.config import WhatsAppConfig

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
def webhook_receiver(config):
    # Pass a dummy router
    router = MessageRouter(client=None)
    return WebhookReceiver(config=config, router=router)

@pytest.fixture
def test_client(webhook_receiver):
    app = webhook_receiver.get_app()
    return TestClient(app)

def test_verify_webhook_success(test_client, config):
    response = test_client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": config.whatsapp_verify_token,
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"

def test_verify_webhook_failure(test_client):
    response = test_client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403

def test_receive_text_message(test_client):
    # A simplified payload similar to WhatsApp API format
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "12345",
                                "phone_number_id": "67890",
                            },
                            "contacts": [{"profile": {"name": "Test User"}, "wa_id": "33612345678"}],
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "id": "wamid.123",
                                    "timestamp": "1630000000",
                                    "text": {"body": "Hello world!"},
                                    "type": "text",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    response = test_client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.text == "OK"
