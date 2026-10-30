import asyncio, re
from .base import Guard, GuardResult, Action

PATTERNS = {
    "override": r"ignore (all |any )?(previous|prior|above) (instructions|rules|prompts)",
    "reveal_prompt": r"(reveal|show|print|repeat).{0,30}(system prompt|hidden instructions|your instructions)",
    "role_hijack": r"you are now|act as (dan|an? unrestricted)|developer mode|do anything now",
    "bypass": r"(bypass|disable|turn off).{0,20}(safety|guardrails|filters?)",
    "exfil": r"(send|post|upload).{0,40}(https?://|api key|password|secret)",
}
COMPILED = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}

class InjectionGuard(Guard):
    name = "injection"

    def __init__(self, threshold: int = 1, delay_ms: float = 0):
        self.threshold = threshold
        self.delay_ms = delay_ms  # simulates a model-backed classifier's latency

    async def check(self, text, ctx):
        if self.delay_ms:
            await asyncio.sleep(self.delay_ms / 1000)
        hits = [k for k, p in COMPILED.items() if p.search(text)]
        if len(hits) >= self.threshold:
            return GuardResult(guard=self.name, action=Action.BLOCK, reason=f"patterns: {hits}")
        return GuardResult(guard=self.name, action=Action.ALLOW)