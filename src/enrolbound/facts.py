"""Read the synthetic site note. No LLM."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.getenv("ENROLBOUND_DATA", ROOT / "data"))
NOTE_PATH = DATA / "patient_note.txt"
PROTOCOL_PATH = DATA / "protocol.md"
HOSTILE_PATH = DATA / "hostile_notice.md"
NHS_RE = re.compile(r"\b(\d{3}\s?\d{3}\s?\d{4})\b")


@dataclass(frozen=True)
class PatientFacts:
    histology: str | None
    egfr_mutation_status: str | None
    ecog: int | None
    takes_metformin: bool
    egfr_value: float | None
    egfr_reported: bool
    nhs_number: str | None
    raw_note: str


def nhs_visible_in_text(text: str, nhs_number: str | None) -> bool:
    if not nhs_number:
        return False
    digits = re.sub(r"\D", "", nhs_number)
    return bool(digits) and digits in re.sub(r"\D", "", text)


def load_note(path: Path | None = None) -> str:
    return (path or NOTE_PATH).read_text(encoding="utf-8")


def load_protocol(path: Path | None = None) -> str:
    return (path or PROTOCOL_PATH).read_text(encoding="utf-8")


def load_hostile(path: Path | None = None) -> str:
    return (path or HOSTILE_PATH).read_text(encoding="utf-8")


def extract_facts(note: str, egfr_unknown: bool = False) -> PatientFacts:
    hist_m = re.search(r"Histology:\s*(.+)", note, re.I)
    mut_m = re.search(r"EGFR uncommon mutation:\s*(.+)", note, re.I)
    ecog_m = re.search(r"ECOG:\s*(\d+)", note, re.I)
    pending = re.search(
        r"eGFR:\s*(not yet reported|unknown|pending|not reported|n/?a)",
        note,
        re.I,
    )
    value_m = re.search(r"eGFR:\s*([\d.]+)", note, re.I)
    nhs_m = NHS_RE.search(note)
    reported = not egfr_unknown and not pending and value_m is not None
    return PatientFacts(
        histology=hist_m.group(1).strip() if hist_m else None,
        egfr_mutation_status=mut_m.group(1).strip() if mut_m else None,
        ecog=int(ecog_m.group(1)) if ecog_m else None,
        takes_metformin="metformin" in note.lower(),
        egfr_value=float(value_m.group(1)) if value_m and not egfr_unknown else None,
        egfr_reported=reported,
        nhs_number=nhs_m.group(1) if nhs_m else None,
        raw_note=note,
    )
