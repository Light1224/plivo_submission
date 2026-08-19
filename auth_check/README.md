# Plivo Auth Check

Quick credential check using Plivo Account API docs endpoint:

- `GET https://api.plivo.com/v1/Account/{auth_id}/`
- Auth: BasicAuth (`auth_id:auth_token`)

Reference:
- https://www.plivo.com/docs/account/api/overview

## Run

```bash
uv run python auth_check/check_plivo_auth.py \
  --auth-id "<AUTH_ID>" \
  --auth-token "<AUTH_TOKEN>"
```

Expected:
- `HTTP 200` => credentials valid
- `HTTP 401` => credentials invalid / token mismatch
