from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from enrolbound.agent import DEFAULT_QUESTION, ECHO_PROMPT, ask_model
from enrolbound.facts import (
    DATA,
    extract_facts,
    load_hostile,
    load_note,
    load_protocol,
    nhs_visible_in_text,
)
from enrolbound.ontology import CRITERIA, QUOTES, evaluate_protocol
from enrolbound.status import snapshot

load_dotenv()

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="SponsorGrid")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

try:
    import logfire

    if os.getenv("LOGFIRE_TOKEN"):
        logfire.configure(service_name="enrolbound")
        logfire.instrument_fastapi(app)
        if hasattr(logfire, "instrument_pydantic_ai"):
            logfire.instrument_pydantic_ai()
except Exception:
    pass


class ScreenRequest(BaseModel):
    switch_on: bool = False
    note: str | None = None
    question: str | None = None
    echo_test: bool = False
    egfr_unknown: bool = False


class ScreenResponse(BaseModel):
    question: str
    switch_on: bool
    engine: str
    failed_rules: list[str]
    unknown_rules: list[str]
    passed_rules: list[str]
    quotes: dict[str, str]
    answer: str
    used_live_model: bool
    live_error: str | None = None
    echo_prompt: str | None = None
    nhs_number_in_note: str | None = Field(default=None)
    nhs_in_answer: bool = False
    pipeline: list[str]


def _pipeline() -> list[str]:
    return [
        "Patient note",
        "Rules engine (no LLM)",
        "Same Agent Python",
        "Gateway (off or on)",
        "Modal model",
    ]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(
        STATIC / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/sources")
def sources() -> FileResponse:
    return FileResponse(DATA / "SOURCES.md")


@app.get("/api/health")
def health() -> dict:
    return snapshot()


@app.get("/api/fixture")
def fixture() -> dict:
    note = load_note()
    facts = extract_facts(note)
    verdict = evaluate_protocol(facts)
    status = snapshot()
    return {
        "study": "SG-ONC-302 (synthetic non-squamous NSCLC excerpt)",
        "question": DEFAULT_QUESTION,
        "questions": [
            "Can I enrol this patient today?",
            "Can I enrol a patient currently taking metformin?",
            "What's the washout for prior immunotherapy?",
            "Is an eGFR of 58 acceptable?",
        ],
        "note": note,
        "protocol": load_protocol(),
        "hostile": load_hostile(),
        "criteria": [{"id": cid, "label": label, "quote": QUOTES[cid]} for cid, label in CRITERIA],
        "engine": verdict.engine,
        "failed_rules": verdict.failed_rules,
        "unknown_rules": verdict.unknown_rules,
        "passed_rules": verdict.passed_rules,
        "quotes": verdict.quotes_for(verdict.failed_rules + verdict.unknown_rules),
        "program": verdict.program_preview,
        "pipeline": _pipeline(),
        "live_gateway": bool(os.getenv("PYDANTIC_AI_GATEWAY_API_KEY", "").strip()),
        "status": status,
        "signoff_token": "6a112dcc",
        "signoff_bound_to": "I3 ECOG performance status 0 or 1",
    }


@app.post("/api/screen", response_model=ScreenResponse)
async def screen(body: ScreenRequest) -> ScreenResponse:
    note = body.note or load_note()
    question = (body.question or DEFAULT_QUESTION).strip() or DEFAULT_QUESTION
    facts = extract_facts(note, egfr_unknown=body.egfr_unknown)
    verdict = evaluate_protocol(facts)
    result = await ask_model(
        question,
        note,
        verdict,
        switch_on=body.switch_on,
        echo_test=body.echo_test,
    )
    return ScreenResponse(
        question=question,
        switch_on=body.switch_on,
        engine=verdict.engine,
        failed_rules=verdict.failed_rules,
        unknown_rules=verdict.unknown_rules,
        passed_rules=verdict.passed_rules,
        quotes=verdict.quotes_for(verdict.failed_rules + verdict.unknown_rules),
        answer=result.answer,
        used_live_model=result.used_live_model,
        live_error=result.live_error,
        echo_prompt=ECHO_PROMPT if body.echo_test else None,
        nhs_number_in_note=facts.nhs_number,
        nhs_in_answer=nhs_visible_in_text(result.answer, facts.nhs_number),
        pipeline=_pipeline(),
    )


class PipelineRequest(BaseModel):
    protocol_text: str | None = None
    trial_id: str | None = None
    switch_on: bool = True
    echo_test: bool = False
    question: str | None = None


@app.post("/api/run-modal-pipeline")
async def run_modal_pipeline(body: PipelineRequest) -> dict:
    """SponsorGrid Modal tab. Same agent, Gateway route off or on."""
    screen_body = ScreenRequest(
        switch_on=body.switch_on,
        question=body.question,
        echo_test=body.echo_test,
    )
    result = await screen(screen_body)
    return {
        "execution_engine": "Modal + Pydantic AI Gateway",
        "protocol_id": body.trial_id or "SG-ONC-302",
        "used_live_model": result.used_live_model,
        "live_error": result.live_error,
        "switch_on": result.switch_on,
        "stdout_log": result.answer,
        "failed_rules": result.failed_rules,
        "unknown_rules": result.unknown_rules,
        "nhs_in_answer": result.nhs_in_answer,
        "structured_primitives": [
            {
                "atom_id": "E2",
                "category": "EXCLUSION",
                "condition_biomarker": "eGFR",
                "operator": "GREATER_THAN_OR_EQUAL",
                "expected_value": 60,
                "unit": "mL/min/1.73m2",
                "essentiality": "CRITICAL",
            },
            {
                "atom_id": "I2",
                "category": "INCLUSION",
                "condition_biomarker": "Uncommon EGFR mutation",
                "operator": "EQUALS",
                "expected_value": "documented",
                "essentiality": "CRITICAL",
            },
        ],
        "candidate_evaluations": [
            {
                "candidate_id": "SYN-NOTE-01",
                "pseudonym": "Priya N.",
                "site_id": "site-cambridge",
                "site_name": "Addenbrooke's Hospital",
                "status": "EXCLUDED" if "E2" in result.failed_rules else "NEAR-MISS",
                "explicitly_met_atoms": result.passed_rules,
                "contradicted_atoms": result.failed_rules,
                "missing_vital_atoms": result.unknown_rules,
                "counterfactual_explanation": result.answer[:400],
            }
        ],
        "site_governance_checks": [],
        "summary_metrics": {
            "total_evaluated": 1,
            "matched_count": 0,
            "near_miss_1_fact_away_count": 1 if result.unknown_rules else 0,
            "excluded_count": 1 if result.failed_rules else 0,
            "sites_evaluated": 1,
            "governance_holds_active": 0,
        },
    }


@app.post("/api/run-both")
async def run_both() -> dict:
    off = await screen(ScreenRequest(switch_on=False))
    on = await screen(ScreenRequest(switch_on=True))
    echo_off = await screen(ScreenRequest(switch_on=False, echo_test=True))
    echo_on = await screen(ScreenRequest(switch_on=True, echo_test=True))
    return {
        "off": off.model_dump(),
        "on": on.model_dump(),
        "echo_off": echo_off.model_dump(),
        "echo_on": echo_on.model_dump(),
    }
