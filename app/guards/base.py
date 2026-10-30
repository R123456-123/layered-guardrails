import time
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel

class Action(str, Enum):
    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"

class GuardResult(BaseModel):
    guard: str
    action: Action
    text: str | None = None   # transformed text if REDACT
    reason: str | None = None
    latency_ms: float = 0.0

class Guard(ABC):
    name: str

    @abstractmethod
    async def check(self, text: str, ctx: dict) -> GuardResult: ...

async def run_guard(guard: "Guard", text: str, ctx: dict) -> GuardResult:
    start = time.perf_counter()
    try:
        res = await guard.check(text, ctx)
    except Exception as e:  # fail closed: a broken guard blocks, never allows
        res = GuardResult(guard=guard.name, action=Action.BLOCK, reason=f"guard_error: {e}")
    res.latency_ms = (time.perf_counter() - start) * 1000
    return res