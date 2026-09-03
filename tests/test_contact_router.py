import pytest

from devtools_inbox.contact_router import DeveloperContact, route_contact


class RecordingSender:
    def __init__(self) -> None:
        self.request: dict[str, str] = {}

    async def send(self, **request: str) -> str:
        self.request = request
        return "msg_build_42"


@pytest.mark.asyncio
async def test_build_event_is_routed_with_pipeline_context() -> None:
    sender = RecordingSender()
    contact = DeveloperContact(
        kind="build_event",
        email="dev@example.com",
        project="artifact-pipeline",
        summary="Linux build stopped",
        details="Stage package-wheel exited before upload.",
    )

    result = await route_contact(contact, sender, "tools@example.com")

    assert result.model_dump() == {"message_id": "msg_build_42", "queue": "build_event"}
    assert sender.request["to"] == "tools@example.com"
    assert sender.request["subject"] == "[Build event] artifact-pipeline: Linux build stopped"
    assert "Queue: build_event" in sender.request["text"]
    assert sender.request["idempotency_key"].startswith("devtools-contact-")
