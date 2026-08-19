from __future__ import annotations

from plivo import plivoxml

from .config import Settings
from .prompts import EN_PROMPTS, ES_PROMPTS


class IvrFlowBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def otp_prompt(self, prefix: str | None = None) -> str:
        response = plivoxml.ResponseElement()

        if prefix:
            response.add(plivoxml.SpeakElement(prefix))

        get_digits = plivoxml.GetDigitsElement(
            action=self.settings.full_url("/webhook/otp"),
            method="POST",
            num_digits=4,
            timeout=7,
        )
        get_digits.add(plivoxml.SpeakElement(EN_PROMPTS["otp_intro"]))
        response.add(get_digits)

        response.add(plivoxml.SpeakElement(EN_PROMPTS["goodbye"]))
        response.add(plivoxml.HangupElement())
        return response.to_string()

    def language_menu(self, prefix: str | None = None) -> str:
        response = plivoxml.ResponseElement()

        if prefix:
            response.add(plivoxml.SpeakElement(prefix))

        get_digits = plivoxml.GetDigitsElement(
            action=self.settings.full_url("/webhook/language"),
            method="POST",
            num_digits=1,
            timeout=7,
        )
        get_digits.add(plivoxml.SpeakElement(EN_PROMPTS["language"]))
        response.add(get_digits)

        response.add(plivoxml.SpeakElement(EN_PROMPTS["goodbye"]))
        response.add(plivoxml.HangupElement())
        return response.to_string()

    def level_two_menu(self, lang: str, prefix: str | None = None) -> str:
        normalized_lang = "es" if lang == "es" else "en"

        response = plivoxml.ResponseElement()

        if prefix:
            response.add(plivoxml.SpeakElement(prefix))

        get_digits = plivoxml.GetDigitsElement(
            action=self.settings.full_url(f"/webhook/action?lang={normalized_lang}"),
            method="POST",
            num_digits=1,
            timeout=7,
        )

        if normalized_lang == "es":
            get_digits.add(plivoxml.SpeakElement(ES_PROMPTS["menu"]))
        else:
            get_digits.add(plivoxml.SpeakElement(EN_PROMPTS["menu"]))

        response.add(get_digits)
        response.add(
            plivoxml.SpeakElement(
                EN_PROMPTS["goodbye"] if normalized_lang == "en" else ES_PROMPTS["goodbye"]
            )
        )
        response.add(plivoxml.HangupElement())
        return response.to_string()

    def play_audio(self, lang: str) -> str:
        normalized_lang = "es" if lang == "es" else "en"

        response = plivoxml.ResponseElement()
        response.add(
            plivoxml.SpeakElement(
                self.settings.audio_help_message_en
                if normalized_lang == "en"
                else self.settings.audio_help_message_es
            )
        )
        response.add(
            plivoxml.SpeakElement(
                "Playing audio now." if normalized_lang == "en" else "Reproduciendo audio ahora."
            )
        )
        response.add(plivoxml.PlayElement(self.settings.audio_file_url))
        response.add(
            plivoxml.SpeakElement(
                EN_PROMPTS["goodbye"] if normalized_lang == "en" else ES_PROMPTS["goodbye"]
            )
        )
        response.add(plivoxml.HangupElement())
        return response.to_string()

    def forward_call(self, lang: str) -> str:
        normalized_lang = "es" if lang == "es" else "en"

        response = plivoxml.ResponseElement()

        if not self.settings.live_associate_number:
            response.add(
                plivoxml.SpeakElement(
                    EN_PROMPTS["associate_unavailable"]
                    if normalized_lang == "en"
                    else ES_PROMPTS["associate_unavailable"]
                )
            )
            response.add(plivoxml.HangupElement())
            return response.to_string()

        response.add(
            plivoxml.SpeakElement(
                EN_PROMPTS["forwarding"] if normalized_lang == "en" else ES_PROMPTS["forwarding"]
            )
        )
        dial = plivoxml.DialElement(caller_id=self.settings.plivo_source_number)
        dial.add(plivoxml.NumberElement(self.settings.live_associate_number))
        response.add(dial)
        return response.to_string()
