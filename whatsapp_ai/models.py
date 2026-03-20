from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- Incoming Webhook Models ---

class WhatsAppMessageText(BaseModel):
    body: str

class WhatsAppMessage(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    text: Optional[WhatsAppMessageText] = None
    type: str

class WhatsAppContactProfile(BaseModel):
    name: str

class WhatsAppContact(BaseModel):
    profile: WhatsAppContactProfile
    wa_id: str

class WhatsAppMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: WhatsAppMetadata
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None

class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str

class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]

class WebhookPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]


# --- Internal Domain Models ---

class MessageEvent(BaseModel):
    """Normalized message event for internal routing."""
    message_id: str
    sender: str
    text: str
    timestamp: str
    raw_payload: dict[str, Any]

# --- Outgoing Message Models ---

class OutgoingText(BaseModel):
    body: str
    preview_url: bool = False

class OutgoingMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: Optional[OutgoingText] = None

class TemplateLanguage(BaseModel):
    code: str

class TemplateComponent(BaseModel):
    type: str
    parameters: List[Dict[str, Any]]

class OutgoingTemplate(BaseModel):
    name: str
    language: TemplateLanguage
    components: Optional[List[TemplateComponent]] = None

class OutgoingTemplateMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: OutgoingTemplate
