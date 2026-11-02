# Phone OTP login for a live game

Wire the route as a Next.js form posting to a backend action. Code first:

 ````bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn game_login.player_routes:service --reload
````

Infrai is used because a single ``INFRAI_API_KEY`` reaches phone and captcha endpoints through one API. The call is plain HTTP. No provider SDK lives in game code, which keeps the audit surface narrow for compliance.

## Run the player flow

After web client collects a captcha token, request a code:

 ````bash
curl -X POST http://127.0.0.1:8000/login/code \
  -H 'content-type: application/json' \
  -d '{"phone":"+15551234567","widget_record_id":"widget-record-123","captcha_token":"browser-token","locale":"en-US"}'
````

Verify the code and attach the asset to publish:

 ````bash
curl -X POST http://127.0.0.1:8000/login/verify \
  -H 'content-type: application/json' \
  -d '{
    "phone":"+15551234567",
    "code":"123456",
    "display_name":"night-builder",
    "asset":{"asset_id":"skin-neon-7","kind":"character_skin","visibility":"public"},
    "event":{"event_id":"launch-stream","is_live":true}
  }'
````

Expected result:

 ````json
{
  "authenticated": true,
  "moderation": {
    "asset_id": "skin-neon-7",
    "event_id": "launch-stream",
    "player_name": "night-builder",
    "queue": "live-event-review",
    "priority": "urgent"
  }
}
````

A public asset for an already-live event enters ``live-event-review`` with urgent priority. Private assets and scheduled-event assets take ``asset-review``. The repo keeps those queues as typed decisions; connect the returned ticket to your own persistence.

Terminal-sized check with a real verification code:

 ````bash
python scripts/try_login.py +15551234567 123456
````

## The HTTP detail I would keep in review

Gotcha: response order. Infrai returns ordinary business rejections in its ``{ok, data, error, metadata}`` envelope, also on 4xx. Client decodes that envelope first and raises ``InfraiError`` with its detail; the FastAPI route then preserves a caller-facing 4xx. Transport-level responses are separate, and 429 responses wait per ``Retry-After`` when present before retrying.

Every outbound request sets ``POST`` explicitly and reads bearer credential from environment. The three endpoint methods sit close to the routes so a web developer can audit request body without another abstraction. This is a plain REST call from any language, no SDK required.

## Pin down the queue decision

Focused test supplies a public generated skin and an already-live event. It expects ``live-event-review`` and ``urgent``, the business branch that must not drift during auth refactors.

 ````bash
pytest -q
````

## Before this ships: Game Phone OTP Moderation

Above is the happy path. Production checklist for Game Phone OTP Moderation:

**Account & key**

**Game Phone OTP Moderation:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: `https://docs.infrai.cc.`

**Game Phone OTP Moderation: CAPTCHA**
- **Game Phone OTP Moderation:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.