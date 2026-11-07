"""Crash-resistant local snapshot storage for offline paper simulations.

Local GitHub runner files are EPHEMERAL. This module alone does not provide
cross-run persistence; a separate durable backend must be reviewed before scheduling.
"""
import json
import os
import tempfile
from decimal import Decimal
from pathlib import Path
from simulator import SYMBOLS, initial_state

SCHEMA_VERSION=1

def validate_state(state):
    if not isinstance(state,dict):
        raise ValueError("State must be an object")
    required={"cash","qty","last_candle_ms","trades","history","peak_equity"}
    if not required.issubset(state):
        raise ValueError("State missing required fields")
    if set(state["qty"])!=set(SYMBOLS):
        raise ValueError("Invalid asset quantities")
    for key in ("cash","peak_equity"):
        value=Decimal(str(state[key]))
        if not value.is_finite() or value<0:
            raise ValueError("Invalid "+key)
    for symbol in SYMBOLS:
        value=Decimal(str(state["qty"][symbol]))
        if not value.is_finite() or value<0:
            raise ValueError("Invalid asset quantity")
    last=state["last_candle_ms"]
    if last is not None and (type(last) is not int or last<0 or last%86400000):
        raise ValueError("Invalid last candle timestamp")
    if not isinstance(state["trades"],list) or not isinstance(state["history"],list):
        raise ValueError("Invalid history")
    return state

def load_state(path):
    """Missing state is NOT automatically treated as a new portfolio."""
    p=Path(path)
    if not p.is_file():
        raise FileNotFoundError("Missing portfolio state; initialize explicitly")
    document=json.loads(p.read_text(encoding="utf-8"))
    if document.get("schema_version")!=SCHEMA_VERSION:
        raise ValueError("Unsupported portfolio state version")
    return validate_state(document["portfolio"])

def save_state(path,state):
    """Atomic replace on the same filesystem; does not solve concurrent writers."""
    validate_state(state)
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+p.name+".",suffix=".tmp",dir=p.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump({"schema_version":SCHEMA_VERSION,"portfolio":state},handle,
                      indent=2,sort_keys=True,allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def initialize_state(path):
    """Explicit one-time initialization; refuse to overwrite any existing state."""
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    state=initial_state()
    validate_state(state)
    with p.open("x",encoding="utf-8") as handle:
        json.dump({"schema_version":SCHEMA_VERSION,"portfolio":state},handle,
                  indent=2,sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    return state
