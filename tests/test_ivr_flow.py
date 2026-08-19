from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def build_client() -> TestClient:
    settings = Settings(
        plivo_auth_id="id",
        plivo_auth_token="token",
        plivo_source_number="+14155550100",
        public_base_url="https://example.ngrok-free.app",
        live_associate_number="+14155550199",
        otp_code="0609",
        default_target_number="+14155550123",
        audio_file_url="https://s3.amazonaws.com/plivocloud/Trumpet.mp3",
        audio_help_message_en="This demo follows the assignment flow.",
        audio_help_message_es="Esta demostracion sigue el flujo.",
    )
    return TestClient(create_app(settings))


def test_answer_returns_otp_prompt_xml() -> None:
    client = build_client()
    response = client.post("/webhook/answer")

    assert response.status_code == 200
    assert "<GetDigits" in response.text
    assert "/webhook/otp" in response.text


def test_wrong_otp_reprompts_otp() -> None:
    client = build_client()
    response = client.post("/webhook/otp", data={"Digits": "1111"})

    assert response.status_code == 200
    assert "Incorrect OTP" in response.text
    assert "/webhook/otp" in response.text


def test_correct_otp_moves_to_language_menu() -> None:
    client = build_client()
    response = client.post("/webhook/otp", data={"Digits": "0609"})

    assert response.status_code == 200
    assert "/webhook/language" in response.text
    assert "For English, press 1" in response.text


def test_language_invalid_reprompts_language() -> None:
    client = build_client()
    response = client.post("/webhook/language", data={"Digits": "8"})

    assert response.status_code == 200
    assert "Invalid selection" in response.text
    assert "/webhook/language" in response.text


def test_level_two_option_one_plays_audio() -> None:
    client = build_client()
    response = client.post("/webhook/action?lang=en", data={"Digits": "1"})

    assert response.status_code == 200
    assert "<Play>" in response.text
    assert "Trumpet.mp3" in response.text


def test_level_two_option_two_forwards_call() -> None:
    client = build_client()
    response = client.post("/webhook/action?lang=en", data={"Digits": "2"})

    assert response.status_code == 200
    assert "<Dial" in response.text
    assert "+14155550199" in response.text
