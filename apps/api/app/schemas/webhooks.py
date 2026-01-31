from pydantic import BaseModel
from typing import Optional, List


class TwilioInboundSMS(BaseModel):
    MessageSid: str
    AccountSid: str
    From: str
    To: str
    Body: str
    NumMedia: Optional[str] = "0"
    MediaUrl0: Optional[str] = None
    MediaUrl1: Optional[str] = None
    MediaUrl2: Optional[str] = None
    MediaContentType0: Optional[str] = None

    @property
    def media_urls(self) -> List[str]:
        urls = []
        for i in range(int(self.NumMedia or 0)):
            url = getattr(self, f"MediaUrl{i}", None)
            if url:
                urls.append(url)
        return urls


class EmailInbound(BaseModel):
    from_email: str
    to_email: str
    subject: str
    body_plain: str
    body_html: Optional[str] = None
    attachments: Optional[List[str]] = None
    message_id: Optional[str] = None


class WebFormSubmission(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    property_address: Optional[str] = None
    unit_number: Optional[str] = None
    issue_description: str
    urgency: Optional[str] = "routine"
    photo_urls: Optional[List[str]] = None
