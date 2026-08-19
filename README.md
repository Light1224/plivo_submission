# Plivo IVR Demo — InspireWorks Technical Assignment

Demo IVR system built with Plivo Voice API demonstrating outbound calling, OTP authentication, and a multi-level voice menu.

---

## System Architecture

![System Architecture](image/Screenshot%202026-08-19%20at%2015.01.09.png)

---

## What It Does

1. Makes an outbound call from a Plivo number to a target phone
2. Prompts the caller to enter a 4-digit OTP (birthdate in DDMM format)
3. Loops until the correct OTP is entered
4. Presents Level 1 — language selection (English / Spanish)
5. Presents Level 2 — based on language:
   - Press `1` → plays a short audio message
   - Press `2` → forwards the call to a live associate
6. Invalid input at any level re-prompts the current menu

---

## Project Structure

```
app/
  config.py          # Settings loaded from .env, validation helpers
  ivr_flow.py        # All Plivo XML generation (OTP, language, action menus)
  plivo_service.py   # Outbound call trigger via Plivo REST API
  prompts.py         # IVR prompt text (English + Spanish)
  main.py            # FastAPI app factory, HTTP routes
  templates/
    index.html       # Minimal web UI to trigger calls

auth_check/
  check_plivo_auth.py  # Standalone credential verification script

tests/
  test_ivr_flow.py   # Webhook flow correctness tests
```

---

## Credentials

| Key | Value |
|-----|-------|
| Auth ID | `MAMTAWMGI0MZCTNTYZZS` |
| Auth Token | set in `.env` |
| Plivo source number | `+918035454161` |
| Live associate number | `+912264236412` |
| OTP (DDMM) | `0609` |
| Receiver number | `+918951296699` |

---

## Setup

**Prerequisites**

- **Python 3.11+**
- **uv** — Python package manager: https://docs.astral.sh/uv/getting-started/installation/
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **ngrok** — public tunnel for Plivo webhooks: https://ngrok.com/download
  ```bash
  brew install ngrok  # macOS
  # or download binary from https://ngrok.com/download
  ```

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Fill in PLIVO_AUTH_TOKEN and PUBLIC_BASE_URL
```

`.env` keys:

```env
PLIVO_AUTH_ID=MAMTAWMGI0MZCTNTYZZS
PLIVO_AUTH_TOKEN=<your_auth_token>
PLIVO_SOURCE_NUMBER=+918035454161
PUBLIC_BASE_URL=https://<your-ngrok-url>
LIVE_ASSOCIATE_NUMBER=+912264236412
OTP_CODE=0609
DEFAULT_TARGET_NUMBER=+918951296699
```

---

## Run

**Terminal 1 — start app:**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — expose webhooks (ngrok required):**
```bash
ngrok http 8000
# copy HTTPS URL → set as PUBLIC_BASE_URL in .env, then restart app
```

**Open UI:**
```
http://localhost:8000
```

> Plivo's webhooks must reach your server publicly. `PUBLIC_BASE_URL` must be your ngrok HTTPS URL — not localhost.

---

## Test

**Run unit tests:**
```bash
uv run pytest -q
```

**Verify credentials:**
```bash
uv run python auth_check/check_plivo_auth.py \
  --auth-id MAMTAWMGI0MZCTNTYZZS \
  --auth-token <your_auth_token>
```

Expected: `HTTP 200 — Auth check: SUCCESS`

---

## Demo Script (for video)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open UI, click **Trigger Outbound Call** | Phone rings at `+918951296699` |
| 2 | Answer call, enter wrong OTP e.g. `1111` | Bot re-prompts: "Incorrect OTP" |
| 3 | Enter correct OTP `0609` | Level 1 menu plays |
| 4 | Press `1` for English | Level 2 menu plays in English |
| 5 | Press `1` | Audio message plays |
| 6 | Trigger again, navigate to Level 2, press `2` | Call forwards to `+912264236412` |

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Web UI |
| `POST` | `/trigger-call` | Initiates outbound call |
| `GET/POST` | `/webhook/answer` | Entry point — OTP prompt |
| `POST` | `/webhook/otp` | OTP validation |
| `POST` | `/webhook/language` | Level 1 — language selection |
| `POST` | `/webhook/action?lang=en\|es` | Level 2 — audio or forward |
| `GET` | `/health` | Health check |
