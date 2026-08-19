# Architecture (Demo-Ready, SOLID-Oriented)

This project is intentionally small, but the design follows clean boundaries so it is easy to explain in a technical demo.

## High-level flow

1. `POST /trigger-call` creates an outbound call through Plivo REST API.
2. Plivo hits `answer_url` webhook.
3. App responds with Plivo XML for OTP prompt.
4. Correct OTP unlocks Level-1 language menu.
5. Language selection leads to Level-2 action menu.
6. Action `1` plays audio; action `2` forwards call.

## Components

- `app/main.py`
  - App factory + route orchestration
  - Thin controller style: validates input and delegates business logic
- `app/config.py`
  - `Settings` model from environment
  - Input/format validators and URL helpers
- `app/ivr_flow.py`
  - `IvrFlowBuilder` encapsulates all Plivo XML generation
- `app/plivo_service.py`
  - `PlivoVoiceService` encapsulates Plivo REST SDK call initiation
- `app/prompts.py`
  - Prompt text constants kept separate from flow logic

## SOLID mapping

- **S — Single Responsibility**
  - Each module has one clear concern (HTTP routing, config, XML flow, external API integration).
- **O — Open/Closed**
  - Add new IVR branches by extending `IvrFlowBuilder` methods without rewriting route plumbing.
- **L — Liskov Substitution**
  - Service boundary (`PlivoVoiceService`) can be swapped/mocked in tests without changing route behavior.
- **I — Interface Segregation**
  - Route handlers depend only on minimal operations they need (trigger call / render XML), not broad shared classes.
- **D — Dependency Inversion**
  - `create_app(settings=...)` supports dependency injection for tests and environment isolation.

## Why this works for the assignment demo

- Clear traceability from assignment requirements to endpoints.
- Deterministic OTP and menu branching behavior.
- Focused tests (`tests/test_ivr_flow.py`) validate IVR transitions and invalid-input loops.
- Minimal UI keeps attention on call-flow correctness.
