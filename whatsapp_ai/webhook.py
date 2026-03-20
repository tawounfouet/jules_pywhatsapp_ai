import logging

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from pydantic import ValidationError

from whatsapp_ai.config import WhatsAppConfig
from whatsapp_ai.models import MessageEvent, WebhookPayload
from whatsapp_ai.router import MessageRouter

logger = logging.getLogger(__name__)


class WebhookReceiver:
    """FastAPI webhook receiver for WhatsApp Cloud API."""

    def __init__(self, config: WhatsAppConfig, router: MessageRouter):
        self.config = config
        self.msg_router = router
        self.api_router = APIRouter()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.api_router.add_api_route(
            "/webhook",
            self.verify_webhook,
            methods=["GET"],
        )
        self.api_router.add_api_route(
            "/webhook",
            self.receive_message,
            methods=["POST"],
        )

    async def verify_webhook(self, request: Request) -> Response:
        """Verify the webhook signature from Meta."""
        params = request.query_params
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == self.config.whatsapp_verify_token:
                logger.info("Webhook verified successfully.")
                return Response(content=challenge, status_code=200)
            else:
                logger.warning("Webhook verification failed (token mismatch).")
                raise HTTPException(status_code=403, detail="Forbidden")

        raise HTTPException(status_code=400, detail="Missing parameters")

    async def receive_message(self, request: Request) -> Response:
        """Process incoming WhatsApp webhooks."""
        body = await request.json()
        logger.debug(f"Incoming webhook payload: {body}")

        try:
            payload = WebhookPayload(**body)
        except ValidationError as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return Response(content="OK", status_code=200)

        # Meta requires returning 200 OK immediately for webhook delivery
        if payload.object != "whatsapp_business_account":
            return Response(content="OK", status_code=200)

        for entry in payload.entry:
            for change in entry.changes:
                value = change.value
                if value.messages:
                    for msg in value.messages:
                        # For now, we only handle text messages
                        text_content = ""
                        if msg.type == "text" and msg.text:
                            text_content = msg.text.body

                        event = MessageEvent(
                            message_id=msg.id,
                            sender=msg.from_,
                            text=text_content,
                            timestamp=msg.timestamp,
                            raw_payload=msg.model_dump(),
                        )
                        # We route the message asynchronously but do not await here
                        # to ensure we return 200 OK fast.
                        # However, for simplicity and testing in FastAPI, we await here.
                        # In production, this should be sent to a background task/queue.
                        await self.msg_router.handle_event(event)

        return Response(content="OK", status_code=200)

    def get_app(self) -> FastAPI:
        """Return a FastAPI app containing the webhook routes."""
        app = FastAPI(title="WhatsApp AI Webhook", version="0.1.0")
        app.include_router(self.api_router)
        return app
