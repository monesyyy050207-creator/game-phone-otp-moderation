from game_login.models import AssetVisibility, LiveEvent, ModerationPriority, PlayerAsset
from game_login.moderation_queue import route_asset


def test_public_asset_for_live_event_enters_urgent_queue() -> None:
    ticket = route_asset(
        "night-builder",
        PlayerAsset(asset_id="skin-neon-7", kind="character_skin", visibility=AssetVisibility.PUBLIC),
        LiveEvent(event_id="launch-stream", is_live=True),
    )

    assert ticket.queue == "live-event-review"
    assert ticket.priority is ModerationPriority.URGENT

