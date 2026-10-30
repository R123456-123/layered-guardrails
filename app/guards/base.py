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