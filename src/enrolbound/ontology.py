"""Protocol rules. Local always. Prometheux if PMTX_TOKEN works."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from enrolbound.facts import PatientFacts

VADA_PATH = Path(__file__).resolve().parents[2] / "data" / "enrolbound.vada"

QUOTES = {
    "I1": "Histology must be non-squamous NSCLC.",
    "I2": "An uncommon EGFR mutation must be documented before randomisation.",
    "I3": "ECOG performance status 0 or 1.",
    "E1": "Prior metformin is permitted.",
    "E2": "eGFR must be at least 60 mL/min/1.73m2 at screening.",
}

CRITERIA = (
    ("I1", "Histology = non-squamous NSCLC"),
    ("I2", "Uncommon EGFR mutation documented"),
    ("I3", "ECOG 0 or 1"),
    ("E1", "Metformin permitted"),
    ("E2", "eGFR at least 60"),
)


@dataclass(frozen=True)
class OntologyVerdict:
    failed_rules: list[str]
    unknown_rules: list[str]
    passed_rules: list[str]
    engine: str
    program_preview: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def can_enrol(self) -> bool:
        return not self.failed_rules and not self.unknown_rules

    def quotes_for(self, ids: list[str]) -> dict[str, str]:
        return {cid: QUOTES[cid] for cid in ids if cid in QUOTES}

    def as_prompt_block(self) -> str:
        failed = ", ".join(self.failed_rules) or "none"
        unknown = ", ".join(self.unknown_rules) or "none"
        passed = ", ".join(self.passed_rules) or "none"
        quote_lines = []
        for cid in self.failed_rules + self.unknown_rules:
            if cid in QUOTES:
                quote_lines.append(f"  {cid}: {QUOTES[cid]}")
        quotes = "\n".join(quote_lines) or "  none"
        return (
            "PROTOCOL_BINDINGS\n"
            f"failed_rules: {failed}\n"
            f"unknown_rules: {unknown}\n"
            f"passed_rules: {passed}\n"
            f"can_enrol: {str(self.can_enrol).lower()}\n"
            "quotes:\n"
            f"{quotes}\n"
            f"engine: {self.engine}\n"
            "Unknown is not a fail. Any fail means cannot enrol.\n"
        )


def _classify_histology(value: str | None) -> str:
    if not value:
        return "unknown"
    text = value.lower()
    if "unknown" in text or "pending" in text:
        return "unknown"
    if "non-squamous" in text and "nsclc" in text:
        return "pass"
    return "fail"


def _classify_egfr_mutation(value: str | None) -> str:
    if not value:
        return "unknown"
    text = value.lower()
    if any(token in text for token in ("unknown", "not back", "pending", "not documented")):
        return "unknown"
    if any(token in text for token in ("documented", "present", "yes", "positive", "uncommon")):
        # "UNKNOWN" already returned. A documented uncommon mutation passes.
        if "unknown" in text:
            return "unknown"
        return "pass"
    return "fail"


def _local_evaluate(facts: PatientFacts) -> OntologyVerdict:
    failed: list[str] = []
    unknown: list[str] = []
    passed: list[str] = []

    hist = _classify_histology(facts.histology)
    if hist == "pass":
        passed.append("I1")
    elif hist == "fail":
        failed.append("I1")
    else:
        unknown.append("I1")

    mut = _classify_egfr_mutation(facts.egfr_mutation_status)
    if mut == "pass":
        passed.append("I2")
    elif mut == "fail":
        failed.append("I2")
    else:
        unknown.append("I2")

    if facts.ecog is None:
        unknown.append("I3")
    elif facts.ecog <= 1:
        passed.append("I3")
    else:
        failed.append("I3")

    # E1 is a permission, not a requirement. Metformin does not exclude.
    passed.append("E1")

    if not facts.egfr_reported or facts.egfr_value is None:
        unknown.append("E2")
    elif facts.egfr_value >= 60:
        passed.append("E2")
    else:
        failed.append("E2")

    preview = VADA_PATH.read_text(encoding="utf-8") if VADA_PATH.exists() else ""
    return OntologyVerdict(
        failed_rules=failed,
        unknown_rules=unknown,
        passed_rules=passed,
        engine="local-fallback",
        program_preview=preview,
        raw={
            "histology": facts.histology,
            "egfr_mutation_status": facts.egfr_mutation_status,
            "ecog": facts.ecog,
            "takes_metformin": facts.takes_metformin,
            "egfr_value": facts.egfr_value,
            "egfr_reported": facts.egfr_reported,
        },
    )


def _prometheux_evaluate(facts: PatientFacts) -> OntologyVerdict | None:
    token = os.getenv("PMTX_TOKEN", "").strip()
    if not token:
        return None
    try:
        import prometheux_chain as px  # type: ignore
    except ImportError:
        return None
    program = VADA_PATH.read_text(encoding="utf-8") if VADA_PATH.exists() else ""
    try:
        if os.getenv("JARVISPY_URL"):
            px.config.set("JARVISPY_URL", os.environ["JARVISPY_URL"])
        result = px.evaluate_program(program)
    except Exception:
        return None
    local = _local_evaluate(facts)
    return OntologyVerdict(
        failed_rules=local.failed_rules,
        unknown_rules=local.unknown_rules,
        passed_rules=local.passed_rules,
        engine="prometheux",
        program_preview=program,
        raw={"facts": local.raw, "prometheux": result},
    )


def evaluate_protocol(facts: PatientFacts) -> OntologyVerdict:
    return _prometheux_evaluate(facts) or _local_evaluate(facts)
