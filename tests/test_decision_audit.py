import unittest
from simulator import signal_audit,initial_state,process_closed_candle
from preview import preview

SYMBOLS=("BTCUSDT","ETHUSDT")
DAY=86400000

class DecisionAuditTests(unittest.TestCase):
    def test_ineligible_reasons_are_explicit(self):
        result=signal_audit({"BTCUSDT":["100"]*201,"ETHUSDT":[str(300-i) for i in range(201)]})
        self.assertFalse(result["BTCUSDT"]["eligible"])
        self.assertEqual(result["BTCUSDT"]["reason"],"below_or_equal_sma200_and_nonpositive_momentum60")
        self.assertFalse(result["ETHUSDT"]["eligible"])
        self.assertIn("sma200",result["ETHUSDT"])
    def test_eligible_reason_and_momentum(self):
        result=signal_audit({s:[str(i+1) for i in range(201)] for s in SYMBOLS})
        self.assertTrue(result["BTCUSDT"]["eligible"])
        self.assertEqual(result["BTCUSDT"]["reason"],"eligible")
        self.assertGreater(float(result["BTCUSDT"]["momentum60_pct"]),0)
    def test_persisted_history_contains_decisions(self):
        state=initial_state()
        t=300*DAY
        closes={s:["100"]*201 for s in SYMBOLS}
        quotes={"BTCUSDT":"50000","ETHUSDT":"2500"}
        result,_,status=process_closed_candle(state,t,closes,quotes,t+1000)
        self.assertEqual(status,"processed")
        self.assertEqual(result["history"][-1]["signals"]["BTCUSDT"]["reason"],
                         "below_or_equal_sma200_and_nonpositive_momentum60")
        self.assertEqual(result["history"][-1]["reference_prices"],quotes)
        self.assertNotIn("signals",state)
    def test_duplicate_preview_does_not_invent_historical_signal(self):
        state=initial_state()
        t=300*DAY
        state["last_candle_ms"]=t
        snapshot={"candle_ms":t,"observed_at_ms":t+1000,
                  "closes":{s:["100"]*201 for s in SYMBOLS},
                  "quotes":{"BTCUSDT":"50000","ETHUSDT":"2500"}}
        result=preview(state,snapshot)
        self.assertEqual(result["status"],"duplicate_skipped")
        self.assertIsNone(result["signals"])
if __name__=="__main__": unittest.main()
