import asyncio
from .base import Guard, GuardResult, Action

class TopicGuard(Guard):
    name = "topic"

    def __init__(self, blocked: list[str], delay_ms: float = 0):
        self.blocked = [b.lower() for b in blocked]
        self.delay_ms = delay_ms

    async def check(self, text, ctx):
        if self.delay_ms:
            await asyncio.sleep(self.delay_ms / 1000)
        t = text.lower()
        hit = next((b for b in self.blocked if b in t), None)
        if hit:
            return GuardResult(guard=self.name, action=Action.BLOCK, reason=f"blocked topic: {hit}")
        return GuardResult(guard=self.name, action=Action.ALLOW)