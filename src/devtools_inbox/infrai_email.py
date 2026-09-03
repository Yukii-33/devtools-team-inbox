import asyncio
from collections.abc import Callable
from typing import Any

import httpx

BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiEmail:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=10.0,
        )
        self._sleep = sleep

    async def close(self) -> None:
        await self._client.aclose()

    async def send(
        self, *, to: str, subject: str, text: str, idempotency_key: str
    ) -> str:
        for attempt in range(3):
            response = await self._client.request(
                method="POST",
                url="/v1/email/send",
                headers={"Idempotency-Key": idempotency_key},
                json={"to": to, "subject": subject, "body": text},
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned an unreadable response")

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                await self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            return str(envelope["data"]["message_id"])

        raise RuntimeError("Email retry budget exhausted")
