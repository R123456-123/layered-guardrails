import asyncio, re
from .base import Guard, GuardResult, Action

PII = {  # order matters: longest/most specific first
    "card": r"(?<!\d)(?:\d[ -]?){13,16}(?!\d)",
    "aadhaar": r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)",
    "phone": r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
    "pan": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
}

class PIIGuard(Guard):
    name = "pii"

    def __init__(self, delay_ms: float = 0):
        self.delay_ms = delay_ms

    async def check(self, text, ctx):
        if self.delay_ms:
            await asyncio.sleep(self.delay_ms / 1000)
        out, found = text, []
        for label, pat in PII.items():
            out, n = re.subn(pat, f"[{label.upper()}_REDACTED]", out)
            if n:
                found.append(label)
        if found:
            return GuardResult(guard=self.name, action=Action.REDACT, text=out, reason=f"pii: {found}")
        return GuardResult(guard=self.name, action=Action.ALLOW)