"""Read-only Binance Spot daily candle validation. No order endpoints."""
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

DAY_MS = 86400000
BASE_URL = "https://api.binance.com/api/v3/klines"

def validate_daily_klines(rows, now_ms, count=201):
    """Return 200+ completed UTC daily closes and last candle close boundary."""
    if not isinstance(rows,list) or len(rows)<count:
        raise ValueError("Insufficient daily candles for SMA200 and momentum60")
    closes=[]
    previous=None
    for row in rows:
        if not isinstance(row,list) or len(row)<7:
            raise ValueError("Malformed Binance kline")
        opened=int(row[0])
        close_time=int(row[6])
        if opened%DAY_MS!=0 or close_time!=opened+DAY_MS-1:
            raise ValueError("Not an aligned UTC 1d candle")
        if previous is not None and opened!=previous+DAY_MS:
            raise ValueError("Missing, repeated, or out-of-order daily candle")
        previous=opened
        try:
            price=Decimal(str(row[4]))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Invalid daily close") from exc
        if not price.is_finite() or price<=0:
            raise ValueError("Invalid daily close")
        closes.append(str(price))
    # The final returned row must be fully closed, not today's developing candle.
    if int(rows[-1][6])>=now_ms:
        raise ValueError("Incomplete last daily candle")
    # Reject stale history: final close must be from the most recent completed UTC day.
    current_midnight=(now_ms//DAY_MS)*DAY_MS
    if int(rows[-1][0])!=current_midnight-DAY_MS:
        raise ValueError("Latest daily candle is stale")
    return {"closes":closes,"candle_ms":current_midnight}

def fetch_completed_daily(symbol, now_ms=None, opener=urlopen):
    """Fetch Binance Spot OHLCV only; fail closed on HTTP/JSON/data errors."""
    if symbol not in ("BTCUSDT","ETHUSDT"):
        raise ValueError("Unsupported Spot symbol")
    if now_ms is None:
        now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
    url=BASE_URL+"?"+urlencode({"symbol":symbol,"interval":"1d","limit":202})
    with opener(url,timeout=15) as response:
        rows=json.load(response)
    # Binance normally returns today's incomplete candle: remove it, then validate.
    if not isinstance(rows,list):
        raise ValueError("Unexpected Binance API response")
    completed=[r for r in rows if isinstance(r,list) and len(r)>=7 and int(r[6])<now_ms]
    return validate_daily_klines(completed,now_ms)
