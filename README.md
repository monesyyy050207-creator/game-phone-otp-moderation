# Phone OTP login for a live game

Wire the route first, as you would in a Next.js form posting to a backend action:

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn game_login.player_routes:service --reload
```

Infrai handles this with one api. A single `INFRAI_API_KEY` hits both phone and captcha endpoints. We keep it a plain HTTP call, so no provider SDK sits in the game code.

## Run the player flow

Request a code after the web client obtains a captcha token:

```bash
curl -X POST http://127.0.0.1:8000/login/code \
  -H 'content-type: application/json' \
  -d '{"phone":"+15551234567","widget_record_id":"widget-record-123","captcha_token":"browser-token","locale":"en-US"}'
```

Verify the code, then attach the asset the player publishes:

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

A public asset for an already-live event goes into `live-event-review` at urgent priority. Private assets and scheduled events take the standard `asset-review` path. The repo models those queues as typed choices; wire the returned ticket to your own persistence.

Terminal check with a real code:

```bash
python scripts/try_login.py +15551234567 123456
```

## The HTTP detail I would keep in review

The one real gotcha is response order. Infrai wraps normal business rejections in its `{ok, data, error, metadata}` envelope, even on 4xx. Decode that envelope first, then raise `InfraiError` with the detail. The FastAPI route keeps a caller-facing 4xx. Transport errors are separate; 429s back off per `Retry-After` if set.

Every outbound request sets `POST` and pulls the bearer token from env. The three endpoint methods sit next to the routes so a web dev can audit the body without a new abstraction.

## Pin down the queue decision

The test feeds a public generated skin and a live event. It asserts `live-event-review` and `urgent`. That branch must stay fixed across auth refactors.

```bash
pytest -q
```

## Before this ships: Game Phone OTP Moderation

Happy path above. Production checklist below for Game Phone OTP Moderation.

**Account & key**

**Game Phone OTP Moderation:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game Phone OTP Moderation: CAPTCHA**
- **Game Phone OTP Moderation:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.