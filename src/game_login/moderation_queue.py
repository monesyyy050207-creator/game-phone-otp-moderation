from .models import AssetVisibility, LiveEvent, ModerationPriority, ModerationTicket, PlayerAsset


def route_asset(player_name: str, asset: PlayerAsset, event: LiveEvent) -> ModerationTicket:
    urgent = event.is_live and asset.visibility is AssetVisibility.PUBLIC
    return ModerationTicket(
        asset_id=asset.asset_id,
        event_id=event.event_id,
        player_name=player_name,
        queue="live-event-review" if urgent else "asset-review",
        priority=ModerationPriority.URGENT if urgent else ModerationPriority.STANDARD,
    )

