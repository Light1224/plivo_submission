from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

from .config import Settings
from .ivr_flow import IvrFlowBuilder
from .plivo_service import OutboundCallRequest, PlivoVoiceService
from .prompts import EN_PROMPTS, ES_PROMPTS


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Plivo IVR Assignment")
    templates_dir = Path(__file__).resolve().parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))
    cfg = settings or Settings.from_env()

    def _credentials_ready() -> bool:
        return bool(cfg.plivo_auth_id and cfg.plivo_auth_token and cfg.plivo_source_number)

    def _resolved_public_base_url(request: Request) -> str:
        if cfg.public_base_url:
            return cfg.public_base_url

        forwarded_host = request.headers.get("x-forwarded-host", "").strip()
        host = (forwarded_host or request.headers.get("host", "")).strip()
        if not host:
            return ""

        forwarded_proto = request.headers.get("x-forwarded-proto", "").strip()
        scheme = forwarded_proto or request.url.scheme
        return f"{scheme}://{host}"

    def _is_local_base_url(base_url: str) -> bool:
        if not base_url:
            return True
        host = (urlparse(base_url).hostname or "").lower()
        return host in {"localhost", "127.0.0.1", "0.0.0.0"}

    def _flow_for_request(request: Request) -> IvrFlowBuilder:
        dynamic_base = _resolved_public_base_url(request)
        flow_settings = cfg if not dynamic_base else replace(cfg, public_base_url=dynamic_base)
        return IvrFlowBuilder(flow_settings)

    def _render_home(
        request: Request,
        *,
        error: str | None = None,
        success: str | None = None,
        default_target: str | None = None,
        status_code: int = 200,
    ):
        effective_base = _resolved_public_base_url(request)
        config_ready = _credentials_ready() and bool(effective_base) and not _is_local_base_url(effective_base)

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "default_target": default_target if default_target is not None else cfg.default_target_number,
                "config_ready": config_ready,
                "public_base_url": effective_base,
                "error": error,
                "success": success,
                "otp_ok": cfg.validate_otp_format(),
            },
            status_code=status_code,
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def home(request: Request):
        return _render_home(request)

    @app.post("/trigger-call")
    def trigger_call(request: Request, target_number: str = Form(...)):
        normalized_target = target_number.strip()

        if not _credentials_ready():
            return _render_home(
                request,
                error="Missing required config. Set PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN, PLIVO_SOURCE_NUMBER.",
                default_target=normalized_target or cfg.default_target_number,
                status_code=400,
            )

        effective_base = _resolved_public_base_url(request)
        if not effective_base or _is_local_base_url(effective_base):
            return _render_home(
                request,
                error="A public base URL is required for webhooks. Open this UI via ngrok URL or set PUBLIC_BASE_URL.",
                default_target=normalized_target or cfg.default_target_number,
                status_code=400,
            )

        if not normalized_target:
            return _render_home(request, error="Target number is required.", status_code=400)

        if not Settings.is_valid_e164(normalized_target):
            return _render_home(
                request,
                error="Target number must be in E.164 format, e.g. +14155550123.",
                default_target=normalized_target,
                status_code=400,
            )

        if not cfg.validate_otp_format():
            return _render_home(
                request,
                error="OTP_CODE must be exactly 4 digits in DDMM format.",
                default_target=normalized_target,
                status_code=400,
            )

        try:
            service = PlivoVoiceService(cfg.plivo_auth_id, cfg.plivo_auth_token)
            request_uuid = service.trigger_outbound_call(
                OutboundCallRequest(
                    from_number=cfg.plivo_source_number,
                    to_number=normalized_target,
                    answer_url=f"{effective_base}/webhook/answer",
                )
            )
        except Exception as exc:
            return _render_home(
                request,
                error=f"Failed to trigger call: {exc}",
                default_target=normalized_target,
                status_code=500,
            )

        return _render_home(
            request,
            success=f"Call initiated successfully. request_uuid={request_uuid}",
            default_target=normalized_target,
        )

    @app.api_route("/webhook/answer", methods=["GET", "POST"], response_class=PlainTextResponse)
    def webhook_answer(request: Request):
        ivr = _flow_for_request(request)
        return PlainTextResponse(ivr.otp_prompt(), media_type="application/xml")

    @app.post("/webhook/otp", response_class=PlainTextResponse)
    def webhook_otp(request: Request, Digits: str | None = Form(default=None)):
        ivr = _flow_for_request(request)
        entered = (Digits or "").strip()

        if entered == cfg.otp_code:
            return PlainTextResponse(ivr.language_menu(), media_type="application/xml")

        return PlainTextResponse(ivr.otp_prompt(prefix=EN_PROMPTS["otp_invalid"]), media_type="application/xml")

    @app.post("/webhook/language", response_class=PlainTextResponse)
    def webhook_language(request: Request, Digits: str | None = Form(default=None)):
        ivr = _flow_for_request(request)
        choice = (Digits or "").strip()

        if choice == "1":
            return PlainTextResponse(ivr.level_two_menu("en"), media_type="application/xml")
        if choice == "2":
            return PlainTextResponse(ivr.level_two_menu("es"), media_type="application/xml")

        return PlainTextResponse(
            ivr.language_menu(prefix=EN_PROMPTS["language_invalid"]),
            media_type="application/xml",
        )

    @app.post("/webhook/action", response_class=PlainTextResponse)
    def webhook_action(request: Request, Digits: str | None = Form(default=None)):
        ivr = _flow_for_request(request)
        lang = (request.query_params.get("lang") or "en").lower()
        lang = "es" if lang == "es" else "en"

        choice = (Digits or "").strip()

        if choice == "1":
            return PlainTextResponse(ivr.play_audio(lang), media_type="application/xml")
        if choice == "2":
            return PlainTextResponse(ivr.forward_call(lang), media_type="application/xml")

        invalid_prefix = EN_PROMPTS["menu_invalid"] if lang == "en" else ES_PROMPTS["menu_invalid"]
        return PlainTextResponse(ivr.level_two_menu(lang, prefix=invalid_prefix), media_type="application/xml")

    return app


app = create_app()
