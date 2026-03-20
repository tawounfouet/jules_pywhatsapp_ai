from typing import List, Optional
from pydantic import BaseModel, Field

# --- Resend Inbound Payload Models ---

class ResendEmailContact(BaseModel):
    email: str
    name: Optional[str] = None

class ResendEmailData(BaseModel):
    id: str
    to: List[ResendEmailContact]
    from_: ResendEmailContact = Field(alias="from")
    subject: str
    text: Optional[str] = None
    html: Optional[str] = None

class ResendPayload(BaseModel):
    type: str
    created_at: str
    data: ResendEmailData
