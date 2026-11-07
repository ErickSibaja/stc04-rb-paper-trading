"""STC-04_RB research-only paper simulator; no order endpoints."""
from decimal import Decimal, ROUND_DOWN
import copy
D=Decimal
SYMBOLS=("BTCUSDT","ETHUSDT")
FEE=D("0.001")
SLIPPAGE=D("0.0005")
TARGET=D("0.25")
START=D("10000")

def signal(closes):
    """Input: chronologically ordered, completed UTC daily closing prices."""
    c=[D(str(x)) for x in closes]
    if len(c)<200 or any(x<=0 for x in c):
        raise ValueError("At least 200 valid completed daily closes required")
    sma=sum(c[-200:])/D(200)
    momentum=c[-1]/c[-61]-1
    return {"close":c[-1],"sma200":sma,"momentum60":momentum,
            "eligible":c[-1]>sma and momentum>0}

def initial_state():
    return {"cash":str(START),"qty":{s:"0" for s in SYMBOLS},
            "last_candle_ms":None,"trades":[],"history":[],"peak_equity":str(START)}

def process_closed_candle(state, candle_ms, closes_by_symbol, observed_prices, observed_at_ms):
    """Process one fully closed UTC daily candle exactly once.

    This is an offline function: prices and completed closes are supplied by caller.
    The caller must verify source authenticity, daily UTC alignment and data freshness.
    The observed execution reference must occur after the daily candle closes.
    """
    if not isinstance(candle_ms, int) or candle_ms < 0 or candle_ms % 86400000 != 0:
        raise ValueError("candle_ms must be UTC midnight close timestamp in milliseconds")
    if not isinstance(observed_at_ms, int) or observed_at_ms < candle_ms:
        raise ValueError("Observation must be at or after candle close")
    last=state.get("last_candle_ms")
    if last is not None:
        if candle_ms == last:
            return copy.deepcopy(state), [], "duplicate_skipped"
        if candle_ms < last:
            raise ValueError("Out-of-order candle; state not changed")
    if set(closes_by_symbol) != set(SYMBOLS) or set(observed_prices) != set(SYMBOLS):
        raise ValueError("Both BTCUSDT and ETHUSDT required")
    signals={s:signal(closes_by_symbol[s]) for s in SYMBOLS}
    result,fills=rebalance(state,observed_prices,signals,str(observed_at_ms))
    result["last_candle_ms"]=candle_ms
    result["history"][-1]["candle_ms"]=candle_ms
    result["history"][-1]["observed_at_ms"]=observed_at_ms
    return result,fills,"processed"

def equity(state,prices):
    return D(state["cash"])+sum(D(state["qty"][s])*D(str(prices[s])) for s in SYMBOLS)

def rebalance(state,prices,signals,timestamp):
    """Illustrative fills at supplied observation prices, not actual exchange executions."""
    state=copy.deepcopy(state)
    px={s:D(str(prices[s])) for s in SYMBOLS}
    if any(x<=0 for x in px.values()):
        raise ValueError("Invalid price")
    before=equity(state,px)
    targets={s:(TARGET if signals[s]["eligible"] else D("0"))*before for s in SYMBOLS}
    cash=D(state["cash"])
    qty={s:D(state["qty"][s]) for s in SYMBOLS}
    fills=[]
    for side in ("SELL","BUY"):
        for s in SYMBOLS:
            difference=targets[s]-qty[s]*px[s]
            if side=="SELL" and difference>=0: continue
            if side=="BUY" and difference<=0: continue
            gross=abs(difference)
            if side=="BUY": gross=min(gross,cash/(1+FEE+SLIPPAGE))
            units=(gross/px[s]).quantize(D("0.00000001"),rounding=ROUND_DOWN)
            if side=="SELL": units=min(units,qty[s])
            if units<=0: continue
            notional=units*px[s]
            cost=notional*(FEE+SLIPPAGE)
            if side=="SELL":
                cash+=notional-cost
                qty[s]-=units
            else:
                cash-=notional+cost
                qty[s]+=units
            fills.append({"symbol":s,"side":side,"qty":str(units),
                          "reference_price":str(px[s]),"fee":str(notional*FEE),
                          "slippage":str(notional*SLIPPAGE),"timestamp":timestamp})
    if cash<0: raise AssertionError("Negative cash")
    state["cash"]=str(cash)
    state["qty"]={s:str(qty[s]) for s in SYMBOLS}
    state["trades"].extend(fills)
    after=equity(state,px)
    peak=max(D(state["peak_equity"]),after)
    state["peak_equity"]=str(peak)
    state["history"].append({"timestamp":timestamp,"equity":str(after),
                             "drawdown_pct":str((after/peak-1)*100),
                             "fills":len(fills)})
    return state,fills

if __name__=="__main__":
    print("STC-04_RB: offline research module only. No network or live orders.")
