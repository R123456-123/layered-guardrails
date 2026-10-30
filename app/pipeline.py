import asyncio
from .guards.base import Action, run_guard
from .agent import run_agent

SAFE_FALLBACK = "Sorry, I can't help with that."

async def run_input_guards(text, guards, ctx=None, parallel=True):
    ctx = ctx or {}
    if parallel:
        results = list(await asyncio.gather(*(run_guard(g, text, ctx) for g in guards)))
    else:
        results = []
        for g in guards:
            r = await run_guard(g, text, ctx)
            results.append(r)
            if r.action == Action.BLOCK:  # serial can short-circuit
                break
    blocked = any(r.action == Action.BLOCK for r in results)
    clean = text
    for r in results:
        if r.action == Action.REDACT and r.text:
            clean = r.text
    return {"blocked": blocked, "text": None if blocked else clean, "results": results}


run_guards = run_input_guards  # same runner works for output guards

def _summ(stage, res):
    return {"stage": stage, "blocked": res["blocked"],
            "guards": [r.model_dump(mode="json", exclude={"text"}) for r in res["results"]]}

async def handle_request(user_text, role, policy, llm, input_guards, output_guards,
                         parallel=True, approved=False, max_retries=2):
    audit = []
    inp = await run_input_guards(user_text, input_guards, parallel=parallel)
    audit.append(_summ("input", inp))
    if inp["blocked"]:
        return {"status": "blocked_input", "response": SAFE_FALLBACK, "audit": audit}

    for attempt in range(max_retries + 1):
        ag = await run_agent(inp["text"], role, policy, llm, approved=approved)
        audit.append({"stage": "agent", "attempt": attempt, "status": ag["status"], "trace": ag["trace"]})
        if ag["status"] == "pending_approval":
            return {"status": "pending_approval",
                    "response": "This action needs human approval.", "audit": audit}
        if ag["text"] is None:
            continue
        out = await run_guards(ag["text"], output_guards, ctx={"context": ag["context"]}, parallel=parallel)
        audit.append(_summ("output", out))
        if not out["blocked"]:
            return {"status": "ok", "response": out["text"], "audit": audit}
    return {"status": "fallback_after_retries", "response": SAFE_FALLBACK, "audit": audit}