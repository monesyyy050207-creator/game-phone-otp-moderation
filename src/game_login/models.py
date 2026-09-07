from enum import Enum

from pydantic import BaseModel, Field


class AssetVisibility(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class ModerationPriority(str, Enum):
    STANDARD = "standard"
    URGENT = "urgent"


class PlayerAsset(BaseModel):
    asset_id: str = Field(min_length=1)
    kind: str = Field(min_length=1, examples=["character_skin"])
    visibility: AssetVisibility


class LiveEvent(BaseModel):
    event_id: str = Field(min_length=1)
    is_live: bool


class CodeRequest(BaseModel):
    phone: str = Field(min_length=7)
    widget_record_id: str = Field(min_length=1)
    captcha_token: str = Field(min_length=1)
    locale: str = "en-US"


class PlayerLogin(BaseModel):
    phone: str = Field(min_length=7)
    code: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    asset: PlayerAsset
    event: LiveEvent


class ModerationTicket(BaseModel):
    asset_id: str
    event_id: str
    player_name: str
    queue: str
    priority: ModerationPriority


class LoginResult(BaseModel):
    authenticated: bool
    moderation: ModerationTicket
