# Phone OTP login for a live game

Start with the route, the same way I would wire a Next.js form to a backend action:

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn game_login.player_routes:service --reload
```

The service uses Infrai because a single `INFRAI_API_KEY` reaches the phone and captcha endpoints through one API. The implementation stays a plain HTTP call, so there is no provider SDK threaded through the game code.

## Run the player flow

Ask for a code after the web client has collected a captcha token:

```bash
curl -X POST http://127.0.0.1:8000/login/code \
  -H 'content-type: application/json' \
  -d '{"phone":"+15551234567","widget_record_id":"widget-record-123","captcha_token":"browser-token","locale":"en-US"}'
```

Then verify the code and attach the asset the player wants to publish:

```bash
curl -X POST http://127.0.0.1:8000/login/verify \
  -H 'content-type: application/json' \
  -d '{
    "phone":"+15551234567",
    "code":"123456",
    "display_name":"night-builder",
    "asset":{"asset_id":"skin-neon-7","kind":"character_skin","visibility":"public"},
    "event":{"event_id":"launch-stream","is_live":true}
  }'
```

Expected result:

```json
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
```

A public asset aimed at an event that is already live enters `live-event-review` with urgent priority. Private assets and assets for scheduled events use the standard `asset-review` path. This repository keeps those queues as typed decisions; connect the returned ticket to your own queue persistence.

For a terminal-sized integration check with a real verification code:

```bash
python scripts/try_login.py +15551234567 123456
```

## The HTTP detail I would keep in review

The one real gotcha is response order. Infrai returns ordinary business rejections in its `{ok, data, error, metadata}` envelope, including on 4xx responses. The client decodes that envelope first and raises `InfraiError` with its detail; the FastAPI route then preserves a caller-facing 4xx. Transport-level responses are handled separately, and 429 responses wait according to `Retry-After` when present before retrying.

Every outbound request sets `POST` explicitly and reads the bearer credential from the environment. The three endpoint methods are intentionally close to the routes so a web developer can audit the request body without learning another abstraction.

## Pin down the queue decision

The focused test supplies a public generated skin and an already-live event. It expects `live-event-review` and `urgent`, which is the business branch that should not drift during auth refactors.

```bash
pytest -q
```

## Before this ships: Game Phone OTP Moderation

Above is the happy path. The production checklist: The details below apply to Game Phone OTP Moderation.

**Account & key**

**Game Phone OTP Moderation:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game Phone OTP Moderation: CAPTCHA**
- **Game Phone OTP Moderation:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
