from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

_E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


@dataclass(frozen=True)
class Settings:
    plivo_auth_id: str
    plivo_auth_token: str
    plivo_source_number: str
    public_base_url: str
    live_associate_number: str
    otp_code: str
    default_target_number: str
    audio_file_url: str
    audio_help_message_en: str
    audio_help_message_es: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            plivo_auth_id=os.getenv("PLIVO_AUTH_ID", "").strip(),
            plivo_auth_token=os.getenv("PLIVO_AUTH_TOKEN", "").strip(),
            plivo_source_number=os.getenv("PLIVO_SOURCE_NUMBER", "").strip(),
            public_base_url=os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/"),
            live_associate_number=os.getenv("LIVE_ASSOCIATE_NUMBER", "").strip(),
            otp_code=os.getenv("OTP_CODE", "1503").strip(),
            default_target_number=os.getenv("DEFAULT_TARGET_NUMBER", "").strip(),
            audio_file_url=os.getenv("AUDIO_FILE_URL", "https://s3.amazonaws.com/plivocloud/Trumpet.mp3").strip(),
            audio_help_message_en=os.getenv(
                "AUDIO_HELP_MESSAGE_EN",
                "This demo follows the assignment flow: OTP, language selection, then level two actions.",
            ).strip(),
            audio_help_message_es=os.getenv(
                "AUDIO_HELP_MESSAGE_ES",
                "Esta demostracion sigue el flujo: OTP, seleccion de idioma y luego acciones de nivel dos.",
            ).strip(),
        )

    def outbound_config_ready(self) -> bool:
        return bool(self.plivo_auth_id and self.plivo_auth_token and self.plivo_source_number and self.public_base_url)

    def full_url(self, path: str) -> str:
        if not self.public_base_url:
            return path
        return f"{self.public_base_url}{path}"

    @staticmethod
    def is_valid_e164(number: str) -> bool:
        return bool(_E164_RE.match(number.strip()))

    def validate_otp_format(self) -> bool:
        return len(self.otp_code) == 4 and self.otp_code.isdigit()
