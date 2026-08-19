from __future__ import annotations

from dataclasses import dataclass

import plivo


@dataclass(frozen=True)
class OutboundCallRequest:
    from_number: str
    to_number: str
    answer_url: str


class PlivoVoiceService:
    def __init__(self, auth_id: str, auth_token: str) -> None:
        self._client = plivo.RestClient(auth_id=auth_id, auth_token=auth_token)

    def trigger_outbound_call(self, request: OutboundCallRequest) -> str:
        response = self._client.calls.create(
            from_=request.from_number,
            to_=request.to_number,
            answer_url=request.answer_url,
            answer_method="POST",
        )

        request_uuid = getattr(response, "request_uuid", None)
        if request_uuid:
            return request_uuid

        if isinstance(response, dict):
            return str(response.get("request_uuid", "unknown"))

        return "unknown"
