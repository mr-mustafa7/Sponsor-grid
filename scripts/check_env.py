"""Print which live tools are ready. Safe to run without secrets."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _has(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def main() -> None:
    rows = [
        ("Local protocol rules", True, "Always on. No key needed."),
        ("Rehearsal web page", True, "http://127.0.0.1:8000"),
        ("Pydantic AI Gateway key", _has("PYDANTIC_AI_GATEWAY_API_KEY"), "Needed for a live model call"),
        ("Logfire token", _has("LOGFIRE_TOKEN"), "Needed for traces the judges open"),
        ("GATEWAY_MODEL", _has("GATEWAY_MODEL"), "gateway/modal:enrolbound"),
        ("GATEWAY_MODEL_ON", _has("GATEWAY_MODEL_ON"), "gateway/modal:enrolbound-on"),
        ("Prometheux token", _has("PMTX_TOKEN"), "Optional. Local rules run if this is empty"),
    ]
    for label, ok, note in rows:
        mark = "ready" if ok else "missing"
        print(f"{mark:8}  {label}  — {note}")


if __name__ == "__main__":
    main()
