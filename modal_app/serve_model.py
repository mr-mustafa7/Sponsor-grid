"""Open-weight model on Modal for Gateway BYOK.

This workspace cannot start a GPU without a payment method, so we serve
dense Qwen2.5-1.5B-Instruct on CPU. Not a mixture-of-experts.

    modal deploy modal_app/serve_model.py
"""

from __future__ import annotations

import modal

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
SERVED_NAME = "enrolbound"
MINUTES = 60

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch",
        "transformers>=4.44",
        "accelerate",
        "starlette",
        "uvicorn",
    )
    .env({"HF_HOME": "/root/.cache/huggingface", "TOKENIZERS_PARALLELISM": "false"})
)

hf_cache_vol = modal.Volume.from_name("enrolbound-hf-cache", create_if_missing=True)
app = modal.App("enrolbound-model")


def _build_api():
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()

    async def health(_request):
        return JSONResponse(
            {"ok": True, "model": SERVED_NAME, "upstream": MODEL_NAME, "api": "starlette"}
        )

    async def list_models(_request):
        return JSONResponse(
            {
                "object": "list",
                "data": [{"id": SERVED_NAME, "object": "model", "owned_by": "enrolbound"}],
            }
        )

    async def chat(request):
        data = await request.json()
        raw_messages = data.get("messages") or []
        messages = []
        for item in raw_messages:
            content = item.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            messages.append({"role": item.get("role", "user"), "content": str(content)})
        if not messages:
            messages = [{"role": "user", "content": "Hello"}]
        max_tokens = int(data.get("max_tokens") or data.get("max_completion_tokens") or 256)
        max_tokens = max(1, min(max_tokens, 512))
        temperature = float(data.get("temperature") if data.get("temperature") is not None else 0.7)
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(prompt, return_tensors="pt")
        output = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=temperature > 0,
            temperature=max(temperature, 0.01),
        )
        prompt_tokens = int(inputs["input_ids"].shape[1])
        new_tokens = output[0][inputs["input_ids"].shape[1] :]
        completion_tokens = int(new_tokens.shape[0])
        text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        return JSONResponse(
            {
                "id": "chatcmpl-enrolbound",
                "object": "chat.completion",
                "model": SERVED_NAME,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
        )

    return Starlette(
        routes=[
            Route("/health", health),
            Route("/v1/models", list_models),
            Route("/v1/chat/completions", chat, methods=["POST"]),
        ]
    )


@app.function(
    image=image,
    cpu=4.0,
    memory=8192,
    timeout=10 * MINUTES,
    scaledown_window=15 * MINUTES,
    volumes={"/root/.cache/huggingface": hf_cache_vol},
)
@modal.asgi_app(requires_proxy_auth=False)
def serve():
    return _build_api()
