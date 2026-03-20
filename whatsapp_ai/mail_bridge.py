import hashlib
import hmac
import json
import logging
import re
from typing import Optional, Tuple

from fastapi import APIRouter, Form, HTTPException, Request, Response
from pydantic import ValidationError

from whatsapp_ai.client import BaseMessagingClient
from whatsapp_ai.config import WhatsAppConfig
from whatsapp_ai.mail_models import ResendPayload

logger = logging.getLogger(__name__)

class MailBridge:
    """
    HTTP Bridge connecting inbound emails (Mailgun, Resend) to messaging channels (WhatsApp).
    """

    def __init__(self, config: WhatsAppConfig, messaging_client: BaseMessagingClient):
        self.config = config
        self.messaging_client = messaging_client
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.router.add_api_route("/mailgun", self.receive_mailgun, methods=["POST"])
        self.router.add_api_route("/resend", self.receive_resend, methods=["POST"])

    def verify_mailgun_signature(self, timestamp: str, token: str, signature: str) -> bool:
        """Verify the HMAC-SHA256 signature from Mailgun."""
        if not self.config.mailgun_signing_key:
            return True  # Verification disabled

        hmac_digest = hmac.new(
            key=self.config.mailgun_signing_key.encode("utf-8"),
            msg=(timestamp + token).encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(str(signature), str(hmac_digest))

    async def verify_resend_signature(self, request: Request, signature: str) -> bool:
        """Verify the HMAC-SHA256 signature from Resend."""
        if not self.config.resend_webhook_secret:
            return True  # Verification disabled

        body = await request.body()
        hmac_digest = hmac.new(
            key=self.config.resend_webhook_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(str(signature), str(hmac_digest))

    def parse_email_target(self, to_address: str, subject: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts channel and target from the 'To' address or the 'Subject'.
        E.g. "whatsapp+23761234567@example.com" -> ("whatsapp", "23761234567")
        E.g. Subject: "whatsapp +23761234567" -> ("whatsapp", "+23761234567")
        """
        # 1. Try to extract from To address alias: channel+target@domain
        # Note: resend/mailgun formats may include name like "John <whatsapp+123@...>"
        email_match = re.search(r"([a-zA-Z0-9_]+)\+([^@]+)@", to_address)
        if email_match:
            return email_match.group(1).lower(), email_match.group(2).strip()

        # 2. Fallback to Subject extraction
        # Assumes format "channel target"
        subject_parts = subject.strip().split(" ", 1)
        if len(subject_parts) == 2:
            return subject_parts[0].lower(), subject_parts[1].strip()

        # Could not determine target
        return None, None

    async def _dispatch(self, channel: str, target: str, message_body: str) -> None:
        """Dispatch the message to the appropriate client."""
        if channel == "whatsapp":
            # For WhatsApp, target should ideally be digits only or with a plus sign.
            # E.g., +23761234567 -> remove the + if needed, depending on Meta API rules
            # Meta API accepts phone numbers without the '+' generally.
            clean_target = target.replace("+", "")
            await self.messaging_client.send_text_message(to=clean_target, text=message_body.strip())
            logger.info(f"Dispatched message to whatsapp target {clean_target}")
        else:
            logger.warning(f"Unsupported channel '{channel}' requested.")

    async def receive_mailgun(
        self,
        recipient: str = Form(...),
        subject: str = Form(...),
        body_plain: str = Form(alias="body-plain", default=""),
        timestamp: str = Form(default=""),
        token: str = Form(default=""),
        signature: str = Form(default=""),
    ) -> Response:
        """Process inbound webhooks from Mailgun."""
        if self.config.mailgun_signing_key and not self.verify_mailgun_signature(timestamp, token, signature):
            raise HTTPException(status_code=403, detail="Invalid Mailgun signature")

        channel, target = self.parse_email_target(recipient, subject)

        if not channel or not target:
            logger.error(f"Could not extract routing info from Mailgun email. Recipient: {recipient}, Subject: {subject}")
            return Response(content="Missing routing info", status_code=200)

        # Dispatch
        try:
            await self._dispatch(channel, target, body_plain)
        except Exception as e:
            logger.error(f"Failed to dispatch Mailgun email: {e}")

        return Response(content="OK", status_code=200)

    async def receive_resend(self, request: Request) -> Response:
        """Process inbound webhooks from Resend."""
        signature = request.headers.get("resend-signature", "")
        if self.config.resend_webhook_secret and not await self.verify_resend_signature(request, signature):
            raise HTTPException(status_code=403, detail="Invalid Resend signature")

        try:
            body = await request.json()
            payload = ResendPayload(**body)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse Resend payload: {e}")
            return Response(content="Invalid JSON or Payload", status_code=400)

        if payload.type != "email.received":
            return Response(content="Ignored non-inbound event", status_code=200)

        # Resend provides multiple recipients, we check the first one
        if not payload.data.to:
            return Response(content="No recipient found", status_code=200)

        recipient_email = payload.data.to[0].email
        subject = payload.data.subject
        body_text = payload.data.text or payload.data.html or ""

        channel, target = self.parse_email_target(recipient_email, subject)

        if not channel or not target:
            logger.error(f"Could not extract routing info from Resend email. Recipient: {recipient_email}, Subject: {subject}")
            return Response(content="Missing routing info", status_code=200)

        try:
            await self._dispatch(channel, target, body_text)
        except Exception as e:
            logger.error(f"Failed to dispatch Resend email: {e}")

        return Response(content="OK", status_code=200)
