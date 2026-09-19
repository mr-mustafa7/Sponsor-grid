"""What is live versus rehearsal. Booleans only. No secrets."""

from __future__ import annotations

import os


def snapshot() -> dict:
    gateway = bool(os.getenv("PYDANTIC_AI_GATEWAY_API_KEY", "").strip())
    logfire = bool(os.getenv("LOGFIRE_TOKEN", "").strip())
    model = os.getenv("GATEWAY_MODEL", "").strip()
    model_on = os.getenv("GATEWAY_MODEL_ON", "").strip()
    modal = any(
        token in (model + " " + model_on).lower()
        for token in ("modal", "enrolbound")
    )
    prometheux = bool(os.getenv("PMTX_TOKEN", "").strip())
    return {
        "gateway_key": gateway,
        "logfire": logfire,
        "modal": modal,
        "prometheux": prometheux,
        "live_model": gateway,
        "next_human_step": _next(gateway, logfire, modal, model_on),
    }


def _next(gateway: bool, logfire: bool, modal: bool, model_on: str) -> str:
    if not gateway:
        return (
            "Join Pydantic Slack #hackathon, create Logfire and a Gateway key, "
            "then put PYDANTIC_AI_GATEWAY_API_KEY in .env."
        )
    if not logfire:
        return "Put LOGFIRE_TOKEN in .env so the two traces are saved."
    if not modal:
        return "Set GATEWAY_MODEL=gateway/enrolbound:enrolbound after Modal BYOK."
    if not model_on:
        return "Set GATEWAY_MODEL_ON=gateway/modal:enrolbound-on for the bound route."
    return (
        "Paste the custom Transform and inbound Redact on enrolbound-on only, "
        "then press Run both sides."
    )
