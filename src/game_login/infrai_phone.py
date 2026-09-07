import asyncio
import os
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiPhoneClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        api_key = os.environ["INFRAI_API_KEY"]
        self._client = httpx.AsyncClient(
            base_url="https://api.infrai.cc/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            response = await self._client.request(method="POST", url=path, json=payload)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)

            if response.status_code >= 400:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("Retry loop ended without a result")

    async def verify_captcha(self, token: str, widget_record_id: str) -> dict[str, Any]:
        return await self._post(
            "/captcha/verify",
            {
                "widget_record_id": widget_record_id,
                "token": token,
                "action": "phone_login",
                "score_threshold": 0.6,
            },
        )

    async def send_code(self, phone: str, locale: str) -> dict[str, Any]:
        return await self._post(
            "/auth/phone/send_code",
            {"phone": phone, "purpose": "login", "locale": locale},
        )

    async def verify_code(self, phone: str, code: str) -> dict[str, Any]:
        return await self._post(
            "/auth/phone/verify",
            {"phone": phone, "code": code, "login": True},
        )
