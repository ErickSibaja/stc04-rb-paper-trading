"""Explicit opt-in single-day paper portfolio commit. NEVER sends exchange orders.

Default mode is read-only. Writing requires --commit and GITHUB_TOKEN with
contents:write. Do not schedule until workflow permissions and replay tests pass.
"""
import argparse
import json
import os
from preview import fetch_market_snapshot,preview
from github_state import load_remote_state,save_remote_state
from simulator import process_closed_candle

def run(repository,token,commit=False,market_loader=fetch_market_snapshot,
        state_loader=load_remote_state,state_writer=save_remote_state):
    state,sha=state_loader(repository,token)
    market=market_loader()
    report=preview(state,market)
    if not commit:
        return {"mode":"preview","report":report,"committed":False}
    # Commit only the latest completed UTC day. Never silently skip an
    # unprocessed day: the strategy is daily and missing sessions require review.
    last=state.get("last_candle_ms")
    if last is not None and market["candle_ms"] != last and market["candle_ms"] != last + 86400000:
        raise ValueError("Gap in daily portfolio state; manual reconciliation required")
    if report["status"]=="duplicate_skipped":
        return {"mode":"commit","report":report,"committed":False,"reason":"already_processed"}
    updated,_,status=process_closed_candle(
        state,market["candle_ms"],market["closes"],market["quotes"],market["observed_at_ms"])
    if status!="processed":
        raise RuntimeError("Unexpected candle status")
    # Optimistic locking: a concurrent update will be rejected by GitHub.
    state_writer(repository,token,updated,sha)
    return {"mode":"commit","report":report,"committed":True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--commit",action="store_true",help="Persist a single paper day")
    args=parser.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    repo=os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise SystemExit("Missing GitHub credentials")
    result=run(repo,token,commit=args.commit)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
