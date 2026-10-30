import time, uuid
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .agent import MockLLM
from .audit import fingerprint, write_audit
from .factory import build_guards
from .pipeline import handle_request
from .policy import load_policy
from .ratelimit import TokenBucket

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

def create_app(policy=None, llm=None, audit_path="logs/audit.jsonl"):
    policy = policy or load_policy()
    llm = llm or MockLLM()
    inp, out = build_guards(policy)
    rl = TokenBucket(policy["rate_limit"]["capacity"], policy["rate_limit"]["refill_per_sec"])
    app = FastAPI(title="Layered Guardrails")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/chat")
    async def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
        rid = str(uuid.uuid4())
        role = policy["api_keys"].get(x_api_key or "")
        if role is None:
            write_audit({"request_id": rid, "status": "rejected_401"}, audit_path)
            raise HTTPException(401, "invalid or missing API key")
        if not rl.allow(x_api_key):
            write_audit({"request_id": rid, "role": role, "status": "rejected_429"}, audit_path)
            raise HTTPException(429, "rate limit exceeded")

        t0 = time.perf_counter()
        # NOTE: `approved` is never taken from the client; approval must come from a reviewer
        result = await handle_request(req.message, role, policy, llm, inp, out)
        write_audit({
            "request_id": rid, "role": role,
            "input_fp": fingerprint(req.message), "input_len": len(req.message),
            "status": result["status"],
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "stages": result["audit"],
        }, audit_path)
        return {"request_id": rid, "status": result["status"], "response": result["response"]}

    return app

app = create_app()