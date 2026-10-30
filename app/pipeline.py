import asyncio
from .guards.base import Action, run_guard

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