import re
from .tools import execute_tool, Verdict

SECRET = "SECRET-CANARY-7731"

class MockLLM:
    """Worst-case model: follows any instruction in its input. Guards are what we test."""
    async def generate(self, messages):
        last = messages[-1]
        if last["role"] == "tool":
            c = last["content"]
            if c.startswith("ERROR:"):
                return {"type": "final", "text": f"I couldn't complete that: {c[7:]}"}
            return {"type": "final", "text": f"Done. {c}"}
        t = last["content"]
        if m := re.search(r"delete (?:the )?(?:file )?(\S+)", t, re.I):
            return {"type": "tool_call", "name": "delete_file", "args": {"path": m.group(1)}}
        if m := re.search(r"email (\S+@\S+) (?:saying|with) (.+)", t, re.I):
            return {"type": "tool_call", "name": "send_email",
                    "args": {"to": m.group(1), "subject": "Hello", "body": m.group(2)}}
        if re.search(r"system prompt|your instructions", t, re.I):
            return {"type": "final", "text": f"My instructions: {SECRET}"}
        if re.search(r"\bcite\b|source for", t, re.I):
            return {"type": "final", "text": "According to https://fake-journal.org/paper/4821 the effect is 73%."}
        if m := re.search(r"search (?:for )?(.+)", t, re.I):
            return {"type": "tool_call", "name": "search_docs", "args": {"query": m.group(1)[:200]}}
        return {"type": "final", "text": f"Here is a helpful answer about: {t}"}

async def run_agent(user_text, role, policy, llm, approved=False, max_steps=4):
    messages = [{"role": "user", "content": user_text}]
    trace, context = [], [user_text]
    for step in range(max_steps):
        out = await llm.generate(messages)
        if out["type"] == "final":
            return {"status": "done", "text": out["text"], "trace": trace, "context": "\n".join(context)}
        res = await execute_tool(out["name"], out["args"], role, policy, approved=approved)
        trace.append({"step": step, "tool": out["name"], "verdict": res["verdict"].value})
        if res["verdict"] == Verdict.NEEDS_APPROVAL:
            return {"status": "pending_approval", "text": None, "trace": trace, "context": "\n".join(context)}
        content = res.get("output") or f"ERROR: {res['reason']}"
        context.append(content)
        messages.append({"role": "tool", "content": content})
    return {"status": "max_steps", "text": None, "trace": trace, "context": "\n".join(context)}