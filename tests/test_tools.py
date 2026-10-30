import asyncio, yaml
from app.tools import execute_tool, Verdict

POLICY = yaml.safe_load(open("policies/policy.yaml"))
run = lambda *a, **k: asyncio.run(execute_tool(*a, policy=POLICY, **k))

def test_unknown_tool_denied():
    assert run("rm_rf", {}, "admin")["verdict"] == Verdict.DENIED

def test_viewer_cannot_email():
    r = run("send_email", {"to": "a@b.com", "subject": "hi", "body": "x"}, "viewer")
    assert r["verdict"] == Verdict.DENIED

def test_analyst_email_needs_approval_then_ok():
    args = {"to": "a@b.com", "subject": "hi", "body": "x"}
    assert run("send_email", args, "analyst")["verdict"] == Verdict.NEEDS_APPROVAL
    assert run("send_email", args, "analyst", approved=True)["verdict"] == Verdict.OK

def test_bad_email_invalid():
    r = run("send_email", {"to": "not-an-email", "subject": "s", "body": "b"}, "analyst")
    assert r["verdict"] == Verdict.INVALID

def test_path_traversal_blocked():
    assert run("delete_file", {"path": "..\\secrets.txt"}, "admin")["verdict"] == Verdict.INVALID