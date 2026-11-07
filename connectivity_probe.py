"""Diagnostic only: never places trades or stores credentials."""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from market_data import validate_daily_klines

HOSTS=("https://data-api.binance.vision","https://api.binance.com","https://api-gcp.binance.com")
SYMBOLS=("BTCUSDT","ETHUSDT")

def probe():
    now=int(datetime.now(timezone.utc).timestamp()*1000)
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"symbols":{}}
    for symbol in SYMBOLS:
        checks=[]
        for host in HOSTS:
            url=f"{host}/api/v3/klines?symbol={symbol}&interval=1d&limit=202"
            try:
                request=urllib.request.Request(url,headers={"User-Agent":"STC04RB-Research-Diagnostic/1.0"})
                with urllib.request.urlopen(request,timeout=12) as response:
                    data=json.load(response)
                if not isinstance(data,list):
                    raise ValueError("Unexpected response (not OHLCV array)")
                complete=[row for row in data if isinstance(row,list) and len(row)>6 and int(row[6])<now]
                validated=validate_daily_klines(complete,now)
                checks.append({"host":host,"status":"OK","count":len(validated["closes"]),
                               "last_closed_at_ms":validated["candle_ms"]})
                break
            except Exception as exc:
                checks.append({"host":host,"status":"FAILED","error":str(exc)[:180]})
        report["symbols"][symbol]=checks
    print(json.dumps(report,indent=2))
    if any(not any(c["status"]=="OK" for c in report["symbols"][s]) for s in SYMBOLS):
        raise SystemExit("Connectivity failed for one or more symbols; no trading actions taken")

if __name__=="__main__":
    probe()
