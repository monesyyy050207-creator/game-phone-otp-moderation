import argparse
import asyncio

from game_login.infrai_phone import InfraiPhoneClient
from game_login.models import AssetVisibility, LiveEvent, PlayerAsset
from game_login.moderation_queue import route_asset


async def run(phone: str, code: str) -> None:
    client = InfraiPhoneClient()
    try:
        await client.verify_code(phone, code)
    finally:
        await client.close()

    ticket = route_asset(
        "night-builder",
        PlayerAsset(asset_id="skin-neon-7", kind="character_skin", visibility=AssetVisibility.PUBLIC),
        LiveEvent(event_id="launch-stream", is_live=True),
    )
    print(ticket.model_dump_json(indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a player OTP and route an asset for review")
    parser.add_argument("phone")
    parser.add_argument("code")
    args = parser.parse_args()
    asyncio.run(run(args.phone, args.code))

