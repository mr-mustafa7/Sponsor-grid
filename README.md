# SponsorGrid

A feasibility desk for one synthetic Phase III lung-cancer trial (SG-ONC-302). It does not answer “how many are eligible.” It answers who fails nothing and is **one fact away**, and which fact that is.

Not a medical device. All patients are fake.


## How it works

Same Python agent. Same question. Two Gateway routes:

- **Off** (`enrolbound`) — no rule. The model can enrol, invent a washout, and read the NHS number.
- **On** (`enrolbound-on`) — custom Transform + inbound NHS Redact. The answer is a protocol verdict. The number is blanked.

You do not change `src/enrolbound/agent.py` to flip the switch.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env
./scripts/run_local.sh
```

Open http://127.0.0.1:8000

Without keys the page still runs in rehearsal. For the live path, put `PYDANTIC_AI_GATEWAY_API_KEY` and `LOGFIRE_TOKEN` in `.env`.

```bash
PYTHONPATH=src .venv/bin/python scripts/run_live_demo.py
```

## Stack

| Piece | Role |
|---|---|
| Modal `enrolbound-model` | Serves the open-weight model |
| Modal `enrolbound-agent` | Hosts this FastAPI app |
| Pydantic AI Gateway | Off vs on routes, Transform, Redact |
| Logfire | Traces |

`.env` is not in this repo.
