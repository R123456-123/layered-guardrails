import asyncio
from enum import Enum
from pydantic import BaseModel, Field, ValidationError, field_validator

class Verdict(str, Enum):
    OK = "ok"
    INVALID = "invalid_args"
    DENIED = "denied"
    NEEDS_APPROVAL = "needs_approval"
    ERROR = "error"

class SearchArgs(BaseModel):
    query: str = Field(min_length=1, max_length=200)

class EmailArgs(BaseModel):
    to: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
    subject: str = Field(max_length=100)
    body: str = Field(max_length=2000)

class DeleteArgs(BaseModel):
    path: str

    @field_validator("path")
    @classmethod
    def no_traversal(cls, v):
        if ".." in v or v.startswith(("/", "\\")) or ":" in v:
            raise ValueError("path traversal / absolute path not allowed")
        return v

# Mock tools: no real side effects, so the demo is safe
async def search_docs(a): return f"results for: {a.query}"
async def send_email(a):  return f"email sent to {a.to}"
async def delete_file(a): return f"deleted {a.path}"

REGISTRY = {  # the allowlist: anything not here cannot run
    "search_docs": dict(schema=SearchArgs, fn=search_docs, scope="search:read",  high_risk=False),
    "send_email":  dict(schema=EmailArgs,  fn=send_email,  scope="email:send",   high_risk=True),
    "delete_file": dict(schema=DeleteArgs, fn=delete_file, scope="files:delete", high_risk=True),
}

async def execute_tool(name, raw_args, role, policy, approved=False, timeout=2.0):
    tool = REGISTRY.get(name)
    if tool is None:
        return {"verdict": Verdict.DENIED, "reason": f"tool '{name}' not in allowlist"}
    try:
        args = tool["schema"](**raw_args)
    except (ValidationError, TypeError) as e:
        return {"verdict": Verdict.INVALID, "reason": str(e)[:200]}
    if tool["scope"] not in policy["roles"].get(role, []):
        return {"verdict": Verdict.DENIED, "reason": f"role '{role}' lacks {tool['scope']}"}
    if tool["high_risk"] and not approved:
        return {"verdict": Verdict.NEEDS_APPROVAL, "reason": "high-risk action queued for human review"}
    try:
        out = await asyncio.wait_for(tool["fn"](args), timeout)
        return {"verdict": Verdict.OK, "output": out}
    except Exception as e:  # includes timeout
        return {"verdict": Verdict.ERROR, "reason": repr(e)}