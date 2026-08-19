# Plivo IVR Technical Assignment (Minimal + Correct)

This project implements the required outbound-call + OTP + multi-level IVR flow using Plivo Voice APIs and Plivo XML.

## What is implemented

- Outbound call trigger via minimal web UI (`/`)
- OTP gate (4-digit DTMF, hardcoded via env `OTP_CODE`)
  - Wrong OTP loops until correct OTP is entered
- Level 1 IVR: language selection
  - `1` = English
  - `2` = Spanish
- Level 2 IVR (after language)
  - `1` = play audio message
  - `2` = forward call to live associate number
- Graceful invalid-input handling at each level (re-prompts current menu)
- Call flow responses are returned as Plivo XML from webhook endpoints

## Tech stack

- Python 3.11+
- FastAPI
- Plivo Python SDK
- `uv` package manager

## Project structure

- `app/main.py` — app factory + HTTP routes (thin controllers)
- `app/config.py` — environment-driven settings and validation helpers
- `app/ivr_flow.py` — Plivo XML call-flow builder (OTP, language, level-2 actions)
- `app/plivo_service.py` — outbound call integration with Plivo REST API
- `app/prompts.py` — IVR prompt text constants
- `app/templates/index.html` — minimal trigger UI
- `tests/test_ivr_flow.py` — flow correctness tests for webhooks
- `.env.example` — required config keys

## Setup (using `uv`)

1. Create virtual env and install deps:

```bash
uv venv
source .venv/bin/activate
uv sync
```

2. Create `.env` from sample (or use the prefilled local `.env`):

```bash
cp .env.example .env
```

3. Fill `.env` values:

- `PLIVO_AUTH_ID`
- `PLIVO_AUTH_TOKEN`
- `PLIVO_SOURCE_NUMBER` (your Plivo number)
- `PUBLIC_BASE_URL` (public URL reachable by Plivo, e.g. ngrok)
- `LIVE_ASSOCIATE_NUMBER` (placeholder or real test destination)
- `OTP_CODE` (DDMM birthday format, e.g. `0609`)

> Note: Because credentials were shared in chat/screenshots, rotate your `Auth Token` after testing for safety.

4. Run tests:

```bash
uv run pytest -q
```

5. Start server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Expose webhooks publicly

Plivo must reach your webhook URLs. Use a tunnel (example with ngrok):

```bash
ngrok http 8000
```

Set `PUBLIC_BASE_URL` to your HTTPS tunnel URL, for example:

```env
PUBLIC_BASE_URL=https://abcd-1234.ngrok-free.app
```

## Run and test

1. Open UI: `http://localhost:8000`
2. Enter receiver number and trigger outbound call.
3. In call (current default target in `.env` is `+918951296699`):
   - Enter wrong OTP once, then correct OTP
   - Select language (Level 1)
   - Choose action (Level 2):
     - `1` play audio
     - `2` forward call

## Endpoints

- `GET /` — minimal web UI
- `POST /trigger-call` — triggers outbound call via Plivo API
- `POST|GET /webhook/answer` — initial answer URL (OTP prompt)
- `POST /webhook/otp` — OTP validation
- `POST /webhook/language` — Level 1 language selection
- `POST /webhook/action?lang=en|es` — Level 2 action routing
- `GET /health` — health check

## Engineering notes

- Secrets are kept out of source code and loaded from `.env`.
- HTTP layer is separated from IVR XML construction and API integration for maintainability.
- Input validation is explicit (`target_number` must be E.164 for outbound trigger).
- The IVR behavior is covered by focused endpoint-level tests.

## Assignment mapping

- **Outbound Call**: `POST /trigger-call`
- **OTP Authentication Layer**: `/webhook/answer` + `/webhook/otp`
- **IVR Menu**: `/webhook/language` + `/webhook/action`
- **Multi-level Flow Handling**: DTMF branching and invalid-input re-prompts across levels
- **Optional Frontend**: minimal UI at `/`
