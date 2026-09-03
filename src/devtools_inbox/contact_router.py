from enum import StrEnum
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class ContactKind(StrEnum):
    BUILD_EVENT = "build_event"
    RELEASE_OPERATION = "release_operation"
    DIAGNOSTIC = "diagnostic"


class DeveloperContact(BaseModel):
    kind: ContactKind
    email: EmailStr
    project: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=160)
    details: str = Field(min_length=1, max_length=4000)


class RoutedContact(BaseModel):
    message_id: str
    queue: str


SUBJECT_LABELS = {
    ContactKind.BUILD_EVENT: "Build event",
    ContactKind.RELEASE_OPERATION: "Release operation",
    ContactKind.DIAGNOSTIC: "Developer diagnostic",
}


async def route_contact(
    contact: DeveloperContact, sender: Any, team_inbox: str
) -> RoutedContact:
    label = SUBJECT_LABELS[contact.kind]
    subject = f"[{label}] {contact.project}: {contact.summary}"
    text = (
        f"Queue: {contact.kind.value}\n"
        f"Project: {contact.project}\n"
        f"Reporter: {contact.email}\n\n"
        f"{contact.details}"
    )
    fingerprint = sha256(contact.model_dump_json().encode()).hexdigest()
    message_id = await sender.send(
        to=team_inbox,
        subject=subject,
        text=text,
        idempotency_key=f"devtools-contact-{fingerprint}",
    )
    return RoutedContact(message_id=message_id, queue=contact.kind.value)
