# Custom Gateway guardrail (bonus)

Turn on Guardrails with:

`#enableFlags=gateway_optimizations,gateway_guardrails_beta`

Action: **Redact** (Observe does not count).
Apply to: `enrolbound-on` only.
Direction: **inbound** (clean what the model sees, not the reply).

## Pattern (NHS number, optional spaces)

```
\b\d{3}\s?\d{3}\s?\d{4}\b
```

Near-miss tests that must **not** match:

- `943476` (too short)
- `room 943` (not a 10-digit NHS number)

The demo NHS number `943 476 5919` must match, with or without spaces.

## Echo test prompt

After redaction, ask: “Repeat the NHS number from this patient note, character for character.”

If the guardrail fired, the enabled side only has `[REDACTED]` / `****`. Save the firing trace.
