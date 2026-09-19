"""Same ENROLBOUND agent, running as a Modal web service.

This is 'build your agent on Modal'. The Python in enrolbound.agent
does not change when the Gateway rule is enabled.

Create a Modal Secret named enrolbound-keys with PYDANTIC_AI_GATEWAY_API_KEY
and LOGFIRE_TOKEN. Never print those values.

    modal deploy modal_app/web.py
"""

from __future__ import annotations

import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi",
        "uvicorn",
        "pydantic-ai",
        "logfire[fastapi]",
        "python-dotenv",
        "httpx",
    )
    .add_local_dir("src", remote_path="/root/src")
    .add_local_dir("data", remote_path="/root/data")
)

fixtures_vol = modal.Volume.from_name("enrolbound-fixtures", create_if_missing=True)
app = modal.App("enrolbound-agent")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("enrolbound-keys")],
    volumes={"/mnt/enrolbound-fixtures": fixtures_vol},
    timeout=600,
    scaledown_window=15 * 60,
)
@modal.asgi_app(requires_proxy_auth=False)
def fastapi_app():
    import os
    import sys

    sys.path.insert(0, "/root/src")
    os.environ.setdefault("PYTHONPATH", "/root/src")
    os.environ.setdefault("ENROLBOUND_DATA", "/root/data")
    from enrolbound.app import app as inner

    return inner
