import re
from .base import Guard, GuardResult, Action

class LeakGuard(Guard):
    name = "leak"
    def __init__(self, canaries): self.canaries = canaries
    async def check(self, text, ctx):
        if any(c in text for c in self.canaries):
            return GuardResult(guard=self.name, action=Action.BLOCK, reason="secret/canary in output")
        return GuardResult(guard=self.name, action=Action.ALLOW)

class GroundednessGuard(Guard):
    """Baseline heuristic: URLs and numbers in the answer must appear in the context."""
    name = "groundedness"
    async def check(self, text, ctx):
        context = ctx.get("context", "")
        urls = [u.rstrip(".,)") for u in re.findall(r"https?://\S+", text)]
        nums = re.findall(r"\d+(?:\.\d+)?", text)
        bad = [x for x in urls + nums if x not in context]
        if bad:
            return GuardResult(guard=self.name, action=Action.BLOCK, reason=f"ungrounded: {bad[:3]}")
        return GuardResult(guard=self.name, action=Action.ALLOW)

class FormatGuard(Guard):
    name = "format"
    def __init__(self, max_len=2000): self.max_len = max_len
    async def check(self, text, ctx):
        if not text.strip() or len(text) > self.max_len:
            return GuardResult(guard=self.name, action=Action.BLOCK, reason="empty or too long")
        return GuardResult(guard=self.name, action=Action.ALLOW)