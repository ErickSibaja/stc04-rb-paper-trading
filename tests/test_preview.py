import unittest
from decimal import Decimal
from simulator import initial_state
from preview import preview

class PreviewTests(unittest.TestCase):
    def snapshot(self):
        t=86400000*300
        return {"host":"fixture","candle_ms":t,"observed_at_ms":t+60000,
                "closes":{s:list(range(1,202)) for s in ("BTCUSDT","ETHUSDT")},
                "quotes":{"BTCUSDT":"50000","ETHUSDT":"2500"}}
    def test_preview_does_not_mutate_state(self):
        state=initial_state()
        result=preview(state,self.snapshot())
        self.assertFalse(result["state_written"])
        self.assertEqual(state,initial_state())
        self.assertEqual(len(result["hypothetical_fills"]),2)
        self.assertLess(Decimal(result["equity_after_usdt"]),Decimal("10000"))
    def test_duplicate_is_noop(self):
        state=initial_state()
        state["last_candle_ms"]=self.snapshot()["candle_ms"]
        result=preview(state,self.snapshot())
        self.assertEqual(result["status"],"duplicate_skipped")
        self.assertEqual(result["hypothetical_fills"],[])
    def test_missing_asset_rejected(self):
        snap=self.snapshot()
        del snap["quotes"]["ETHUSDT"]
        with self.assertRaises(ValueError):
            preview(initial_state(),snap)
if __name__=="__main__": unittest.main()
