"""Run the judged demo path: same question off vs on, then echo test. No secrets."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from enrolbound.agent import DEFAULT_QUESTION, ECHO_PROMPT, ask_model
from enrolbound.facts import extract_facts, load_note
from enrolbound.ontology import evaluate_protocol


def _safe(text: str) -> str:
    return text.replace("943 476 5919", "[NHS]").replace("9434765919", "[NHS]")


async def one(label: str, switch_on: bool, echo: bool) -> None:
    note = load_note()
    facts = extract_facts(note)
    verdict = evaluate_protocol(facts)
    question = DEFAULT_QUESTION if not echo else ECHO_PROMPT
    result = await ask_model(question, note, verdict, switch_on=switch_on, echo_test=echo)
    print(f"=== {label} ===")
    print(f"live={result.used_live_model} error={result.live_error}")
    print(_safe(result.answer)[:800])
    print()


async def main() -> None:
    os.environ.setdefault("OPENAI_TIMEOUT", "180")
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    if os.getenv("LOGFIRE_TOKEN", "").strip():
        try:
            import logfire

            logfire.configure(service_name="sponsorgrid-live-demo")
            if hasattr(logfire, "instrument_pydantic_ai"):
                logfire.instrument_pydantic_ai()
        except Exception as exc:
            print("logfire_configure_failed", type(exc).__name__)
    await one("OFF same question", False, False)
    await one("ON same question", True, False)
    await one("OFF echo", False, True)
    await one("ON echo", True, True)


if __name__ == "__main__":
    asyncio.run(main())
