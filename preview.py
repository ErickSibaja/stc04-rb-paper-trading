"""Read-only end-to-end preview: market -> signals -> virtual rebalance.

No persistence writes. No orders. All results are hypothetical.
"""
import json
import os
import time
from datetime import datetime,timezone
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from decimal import Decimal
from github_state import load_remote_state
from market_data import validate_daily_klines
from simulator import SYMBOLS,process_closed_candle,equity,signal_audit

HOSTS=("https://data-api.binance.vision","https://api.binance.com","https://api-gcp.binance.com")
DAY_MS=86400000
MAX_QUOTE_AGE_MS=120000

def fetch_market_snapshot(now_ms=None,opener=urlopen):
    """One official Spot host must provide both pairs and their quotes."""
    if now_ms is None:
        now_ms=int(time.time()*1000)
    failures=[]
    for host in HOSTS:
        try:
            candles={}
            quotes={}
            for symbol in SYMBOLS:
                path="/api/v3/klines?"+urlencode({"symbol":symbol,"interval":"1d","limit":202})
                req=Request(host+path,headers={"User-Agent":"STC04RB-ReadOnly/1.0"})
                with opener(req,timeout=15) as resp:
                    rows=json.load(resp)
                if not isinstance(rows,list):
                    raise ValueError("Invalid candle response")
                completed=[r for r in rows if isinstance(r,list) and len(r)>6 and int(r[6])<now_ms]
                candles[symbol]=validate_daily_klines(completed,now_ms)
            candle_ms=candles[SYMBOLS[0]]["candle_ms"]
            if any(candles[s]["candle_ms"]!=candle_ms for s in SYMBOLS):
                raise ValueError("Assets do not share a completed UTC day")
            for symbol in SYMBOLS:
                req=Request(host+"/api/v3/ticker/price?"+urlencode({"symbol":symbol}),
                            headers={"User-Agent":"STC04RB-ReadOnly/1.0"})
                with opener(req,timeout=15) as resp:
                    result=json.load(resp)
                price=Decimal(str(result["price"]))
                if not price.is_finite() or price<=0:
                    raise ValueError("Invalid quote")
                quotes[symbol]=str(price)
            observed_at_ms=int(time.time()*1000)
            if observed_at_ms<now_ms or observed_at_ms-now_ms>MAX_QUOTE_AGE_MS:
                raise ValueError("Quote collection took too long")
            return {"host":host,"candle_ms":candle_ms,"observed_at_ms":observed_at_ms,
                    "closes":{s:candles[s]["closes"] for s in SYMBOLS},"quotes":quotes}
        except Exception as exc:
            failures.append(host+": "+str(exc)[:150])
    raise RuntimeError("All official Binance Spot hosts failed: "+"; ".join(failures))

def preview(state,snapshot):
    if set(snapshot["closes"])!=set(SYMBOLS) or set(snapshot["quotes"])!=set(SYMBOLS):
        raise ValueError("Missing market data")
    before=equity(state,snapshot["quotes"])
    result,fills,status=process_closed_candle(
        state,snapshot["candle_ms"],snapshot["closes"],snapshot["quotes"],
        snapshot["observed_at_ms"])
    after=equity(result,snapshot["quotes"])
    audit=(result["history"][-1].get("signals") if status=="processed" else None)
    return {"status":status,"signals":audit,
            "reference_prices":snapshot["quotes"],
            "signal_note":"Previously processed: historical signals not recomputed as past evidence" if status=="duplicate_skipped" else "Signals computed from completed daily candles",
            "candle_close_utc":datetime.fromtimestamp(
                snapshot["candle_ms"]/1000,timezone.utc).isoformat(),
            "observed_at_utc":datetime.fromtimestamp(
                snapshot["observed_at_ms"]/1000,timezone.utc).isoformat(),
            "source":snapshot.get("host","test fixture"),
            "equity_before_usdt":str(before),"equity_after_usdt":str(after),
            "hypothetical_fills":fills,"cash_after_usdt":result["cash"],
            "quantities_after":result["qty"],"state_written":False}

def main():
    token=os.environ.get("GITHUB_TOKEN")
    repo=os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise SystemExit("Missing read-only GitHub credentials")
    state,_=load_remote_state(repo,token)
    snapshot=fetch_market_snapshot()
    print(json.dumps(preview(state,snapshot),indent=2))
    print("READ-ONLY PREVIEW COMPLETE. NO STATE CHANGES.")

if __name__=="__main__":
    main()
