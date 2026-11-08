"""Independent STC-04_RB daily LONG-only EURUSD study. No state writes, no orders."""
import csv,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
DAY=86400000
FEE=D("0.001");SLIP=D("0.0005");TARGET=D("0.25")
START=D("10000")
def read(path):
    with open(path,newline="") as f:
        rows=list(csv.DictReader(f))
    out=[(int(r["timestamp"]),*[D(r[k]) for k in ("open","high","low","close")]) for r in rows]
    if not out or any(out[i][0]<=out[i-1][0] for i in range(1,len(out))):raise ValueError("Invalid time ordering")
    for t,o,h,l,c in out:
        if not 0<l<=min(o,c)<=max(o,c)<=h:raise ValueError("Invalid OHLC")
    return out
def daily_quotes(bid,ask):
    if len(bid)!=len(ask):raise ValueError("Unpaired BID/ASK")
    days={}
    for b,a in zip(bid,ask):
        if b[0]!=a[0]:raise ValueError("Timestamp mismatch")
        if any(a[k]<b[k] for k in range(1,5)):raise ValueError("Negative spread")
        day=b[0]//DAY*DAY
        if day not in days:days[day]=[]
        days[day].append((b,a))
    out=[]
    for day,rows in sorted(days.items()):
        # Reject short or anomalous sessions; no fabricated daily candles.
        if len(rows)<12:continue
        # The day's close and the NEXT available hourly open are separate events.
        out.append((day,(rows[-1][0][4]+rows[-1][1][4])/2,
                    rows[0][0][1],rows[0][1][1],len(rows)))
    return out
def simulate(days,start,end):
    cash=START;qty=D(0);curve=[];fills=[];eligible_count=0
    # Each signal is calculated using the preceding completed day, then
    # executed on the first observed BID/ASK open of the following session.
    for i in range(start,end):
        day,close,bid_open,ask_open,n=days[i]
        history=[x[1] for x in days[max(0,i-201):i]]
        if len(history)<200:raise ValueError("Insufficient completed warmup")
        sma=sum(history[-200:])/D(200)
        momentum=history[-1]/history[-61]-1
        eligible=history[-1]>sma and momentum>0
        eligible_count+=int(eligible)
        # Mark and rebalance at the current session's executable open.
        mid=(bid_open+ask_open)/2
        before=cash+qty*mid
        target=before*TARGET if eligible else D(0)
        difference=target-qty*mid
        if difference>0:
            px=ask_open*(1+SLIP)
            units=min(difference/px,cash/(px*(1+FEE)))
            if units>0:
                cost=units*px*FEE;cash-=units*px+cost;qty+=units
                fills.append({"day":day,"side":"BUY","units":str(units),"cost_usd":str(cost)})
        elif difference<0:
            px=bid_open*(1-SLIP)
            units=min(qty,-difference/mid)
            if units>0:
                cost=units*px*FEE;cash+=units*px-cost;qty-=units
                fills.append({"day":day,"side":"SELL","units":str(units),"cost_usd":str(cost)})
        # Mark to next day open where available, without opening new trades.
        curve.append(float(cash+qty*mid))
    # Liquidate at last observed BID, charging the same modelled costs.
    last=days[end-1]
    if qty:
        px=last[2]*(1-SLIP)
        cash+=qty*px*(1-FEE)
        fills.append({"day":last[0],"side":"FINAL_SELL","units":str(qty)})
        qty=D(0)
    curve[-1]=float(cash)
    peak=float(START);dd=0
    for v in curve:peak=max(peak,v);dd=min(dd,v/peak-1)
    return {"return_pct":100*(float(cash/START)-1),"max_drawdown_pct":100*dd,
            "rebalance_fills":len(fills),"eligible_sessions":eligible_count,
            "first_day":days[start][0],"last_day":days[end-1][0],
            "fills_sha256":hashlib.sha256(json.dumps(fills,sort_keys=True).encode()).hexdigest()}
def main():
    root=Path("forex-data");out=Path("forex-results");out.mkdir(exist_ok=True)
    paths=[root/f"eurusd-h1-{side}.csv" for side in ("bid","ask")]
    bid,ask=map(read,paths)
    days=daily_quotes(bid,ask)
    # Require history before 2025; research is strictly 2025-01 through 2026-09.
    test=[i for i,d in enumerate(days) if 1735689600000<=d[0]<1790812800000]
    if len(test)<300:raise ValueError("Too few research sessions")
    first=test[0];last=test[-1]+1;n=last-first
    segments={}
    for name,a,b in (("development",0,int(n*.6)),("validation",int(n*.6),int(n*.8)),("holdout",int(n*.8),n)):
        segments[name]=simulate(days,first+a,first+b)
    report={"status":"research_only","strategy":"STC-04_RB","instrument":"EURUSD",
            "timeframe":"daily UTC","market":"forex","segments":segments,
            "sources":[{"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
            "model":{"sma":200,"momentum":60,"allocation":0.25,"long_only":True,
                     "fee_bps":10,"slippage_bps":5,"entry":"next available session open",
                     "signal":"prior completed UTC day"},
            "limitations":["Forex EURUSD LONG is a base-currency exposure; no shorting",
                           "Swap/rollover and financing NOT modeled",
                           "Synthetic portfolio treats USD cash as collateral and EUR long as asset",
                           "Dukascopy quotes not executable broker fills",
                           "USD 10000 virtual starting equity per segment",
                           "Session days with fewer than 12 hourly bars excluded",
                           "No claim of live-trading profitability"]}
    (out/"study_results.json").write_text(json.dumps(report,indent=2))
    lines=["# STC-04_RB — EUR/USD daily research","","Research only; swap/rollover not modeled.","",
           "| Segment | Return | Max DD | Rebalance fills | Eligible sessions |",
           "|---|---:|---:|---:|---:|"]
    for name,r in segments.items():
        lines.append(f'| {name} | {r["return_pct"]:.2f}% | {r["max_drawdown_pct"]:.2f}% | {r["rebalance_fills"]} | {r["eligible_sessions"]} |')
    (out/"STC04_FOREX_REPORT.md").write_text("\n".join(lines)+"\n")
if __name__=="__main__":main()
