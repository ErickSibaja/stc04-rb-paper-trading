"""Opt-in durable GitHub state backend for paper trading only.

Never import this module in the read-only validation workflow. No writes happen
unless save_remote_state is explicitly called with a GitHub token.
"""
import base64
import json
import urllib.error
import urllib.request
from state_store import SCHEMA_VERSION, validate_state

STATE_BRANCH="paper-state"
STATE_PATH="state.json"

def _request(url, token, method="GET", payload=None, opener=urllib.request.urlopen):
    if not token:
        raise ValueError("Missing GitHub token")
    data=json.dumps(payload).encode("utf-8") if payload is not None else None
    req=urllib.request.Request(url,data=data,method=method,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "Content-Type":"application/json",
        "User-Agent":"STC04RB-paper-state"})
    with opener(req,timeout=15) as response:
        return json.load(response)

def load_remote_state(repository,token,opener=urllib.request.urlopen):
    """Return (validated portfolio, current blob SHA) for optimistic locking."""
    if not repository or "/" not in repository:
        raise ValueError("Invalid repository")
    url=f"https://api.github.com/repos/{repository}/contents/{STATE_PATH}?ref={STATE_BRANCH}"
    result=_request(url,token,opener=opener)
    if result.get("encoding")!="base64" or not result.get("sha"):
        raise ValueError("Invalid GitHub state response")
    doc=json.loads(base64.b64decode(result["content"]).decode("utf-8"))
    if doc.get("schema_version")!=SCHEMA_VERSION:
        raise ValueError("Unsupported state schema")
    return validate_state(doc["portfolio"]),result["sha"]

def save_remote_state(repository,token,state,expected_sha,opener=urllib.request.urlopen):
    """Atomic compare-and-swap update: GitHub rejects stale SHA with 409/422.

    Caller must never retry a conflicting write blindly; reload and reconcile.
    A workflow using this must have contents:write and concurrency protection.
    """
    validate_state(state)
    if not expected_sha:
        raise ValueError("Expected SHA is required to avoid overwrites")
    doc={"schema_version":SCHEMA_VERSION,"portfolio":state}
    content=base64.b64encode((json.dumps(doc,sort_keys=True,indent=2)+"\n").encode()).decode()
    url=f"https://api.github.com/repos/{repository}/contents/{STATE_PATH}"
    return _request(url,token,method="PUT",payload={
        "message":"paper: persist completed daily simulation state",
        "content":content,"sha":expected_sha,"branch":STATE_BRANCH},opener=opener)
