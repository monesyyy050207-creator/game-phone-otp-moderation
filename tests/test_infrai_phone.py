import httpx
import pytest

from game_login.infrai_phone import InfraiError, InfraiPhoneClient


@pytest.mark.asyncio
async def test_business_rejection_is_read_from_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")

    async def reject(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(
            400,
            json={"ok": False, "data": None, "error": {"code": "INVALID_INPUT", "message": "Check the code"}, "metadata": {}},
        )

    client = InfraiPhoneClient(transport=httpx.MockTransport(reject))
    with pytest.raises(InfraiError) as caught:
        await client.verify_code("+15551234567", "000000")
    await client.close()

    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_INPUT"

