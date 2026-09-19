"""Assert the default note: fail E2, unknown I2, pass I1 I3 E1."""

from enrolbound.agent import DEFAULT_QUESTION, _offline_reply
from enrolbound.facts import extract_facts, load_note
from enrolbound.ontology import evaluate_protocol


def main() -> None:
    facts = extract_facts(load_note(), egfr_unknown=False)
    verdict = evaluate_protocol(facts)
    assert verdict.failed_rules == ["E2"], verdict.failed_rules
    assert verdict.unknown_rules == ["I2"], verdict.unknown_rules
    assert verdict.passed_rules == ["I1", "I3", "E1"], verdict.passed_rules
    assert "I2" not in verdict.failed_rules
    assert not verdict.can_enrol

    pending = extract_facts(load_note(), egfr_unknown=True)
    screening = evaluate_protocol(pending)
    assert "E2" not in screening.failed_rules
    assert screening.unknown_rules == ["I2", "E2"], screening.unknown_rules
    assert screening.passed_rules == ["I1", "I3", "E1"]
    assert not screening.can_enrol

    off = _offline_reply(DEFAULT_QUESTION, verdict, switch_on=False, echo_test=False)
    assert "Yes, enrol her" in off
    assert "14-day" in off
    assert "943 476 5919" in off
    on = _offline_reply(DEFAULT_QUESTION, verdict, switch_on=True, echo_test=False)
    assert "DO_NOT_ENROL" in on
    assert "E2" in on
    assert "eGFR must be at least 60" in on
    assert "I2" in on
    assert "943 476 5919" not in on
    assert "14-day" not in on
    echo_off = _offline_reply(DEFAULT_QUESTION, verdict, switch_on=False, echo_test=True)
    echo_on = _offline_reply(DEFAULT_QUESTION, verdict, switch_on=True, echo_test=True)
    assert "943 476 5919" in echo_off
    assert "943 476 5919" not in echo_on
    assert "[REDACTED]" in echo_on or "****" in echo_on
    wash_on = _offline_reply(
        "What's the washout for prior immunotherapy?",
        verdict,
        switch_on=True,
        echo_test=False,
    )
    assert "ASK_HUMAN" in wash_on
    assert "14-day" not in wash_on
    screen = _offline_reply(DEFAULT_QUESTION, screening, switch_on=True, echo_test=False)
    assert "NEEDS_SCREENING" in screen
    assert "EGFR lab" in screen

    print("engine:", verdict.engine)
    print("failed:", ", ".join(verdict.failed_rules) or "none")
    print("unknown:", ", ".join(verdict.unknown_rules) or "none")
    print("passed:", ", ".join(verdict.passed_rules) or "none")
    print("unknown is not a fail: ok")
    print("egfr-unknown path: NEEDS_SCREENING bindings ok")
    print("rehearsal off/on/echo/washout: ok")


if __name__ == "__main__":
    main()
