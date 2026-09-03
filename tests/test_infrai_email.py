import httpx
import pytest

from devtools_inbox.infrai_email import InfraiEmail


@pytest.mark.asyncio
async def test_send_decodes_envelope_and_sets_request_boundary() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/email/send"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Idempotency-Key"] == "contact-42"
        assert request.read() == b'{"to":"team@example.com","subject":"Build","body":"Done"}'
        return httpx.Response(200, json={"ok": True, "data": {"message_id": "msg_42"}, "error": None, "metadata": {}})

    sender = InfraiEmail("test-key", transport=httpx.MockTransport(handler))
    try:
        message_id = await sender.send(
            to="team@example.com",
            subject="Build",
            text="Done",
            idempotency_key="contact-42",
        )
    finally:
        await sender.close()

    assert message_id == "msg_42"
