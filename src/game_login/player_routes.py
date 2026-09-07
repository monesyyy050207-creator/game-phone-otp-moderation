from fastapi import FastAPI, HTTPException, Request

from .infrai_phone import InfraiError, InfraiPhoneClient
from .models import CodeRequest, LoginResult, PlayerLogin
from .moderation_queue import route_asset

service = FastAPI(title="Game phone login")


def client_for(request: Request) -> InfraiPhoneClient:
    return request.app.state.infrai


@service.on_event("startup")
async def open_client() -> None:
    service.state.infrai = InfraiPhoneClient()


@service.on_event("shutdown")
async def close_client() -> None:
    await service.state.infrai.close()


def client_error(error: InfraiError) -> HTTPException:
    status = error.status_code if 400 <= error.status_code < 500 else 502
    return HTTPException(status_code=status, detail={"code": error.code, "message": str(error)})


@service.post("/login/code", status_code=202)
async def request_login_code(body: CodeRequest, request: Request) -> dict[str, str]:
    infrai = client_for(request)
    try:
        await infrai.verify_captcha(body.captcha_token, body.widget_record_id)
        await infrai.send_code(body.phone, body.locale)
    except InfraiError as error:
        raise client_error(error) from error
    return {"status": "code_sent"}


@service.post("/login/verify", response_model=LoginResult)
async def verify_login(body: PlayerLogin, request: Request) -> LoginResult:
    try:
        await client_for(request).verify_code(body.phone, body.code)
    except InfraiError as error:
        raise client_error(error) from error

    ticket = route_asset(body.display_name, body.asset, body.event)
    return LoginResult(authenticated=True, moderation=ticket)
