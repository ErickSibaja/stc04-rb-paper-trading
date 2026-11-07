import unittest
from decimal import Decimal as D
from simulator import signal, initial_state, rebalance, equity, SYMBOLS, process_closed_candle

class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.p={"BTCUSDT":D("50000"),"ETHUSDT":D("2500")}
        self.on={s:{"eligible":True} for s in SYMBOLS}
        self.off={s:{"eligible":False} for s in SYMBOLS}
    def test_signal(self):
        self.assertTrue(signal(list(range(1,202)))["eligible"])
        self.assertFalse(signal([D("100")]*200)["eligible"])
    def test_entry(self):
        state,fills=rebalance(initial_state(),self.p,self.on,"t")
        self.assertEqual(len(fills),2)
        self.assertGreaterEqual(D(state["cash"]),0)
        self.assertLess(equity(state,self.p),D("10000"))
    def test_exit(self):
        state,_=rebalance(initial_state(),self.p,self.on,"t")
        state,fills=rebalance(state,self.p,self.off,"t2")
        self.assertEqual([x["side"] for x in fills],["SELL","SELL"])
    def test_no_repeat_at_unchanged_prices(self):
        state,_=rebalance(initial_state(),self.p,self.on,"t")
        _,fills=rebalance(state,self.p,self.on,"t2")
        self.assertFalse(any(x["side"]=="BUY" for x in fills))

    def test_daily_idempotency(self):
        closes={s:list(range(1,202)) for s in SYMBOLS}
        state,fills,status=process_closed_candle(initial_state(),86400000*300,closes,self.p,86400000*300+60000)
        self.assertEqual(status,"processed")
        self.assertEqual(len(fills),2)
        state2,fills2,status2=process_closed_candle(state,86400000*300,closes,self.p,86400000*300+60000)
        self.assertEqual(status2,"duplicate_skipped")
        self.assertEqual(fills2,[])
        self.assertEqual(state2,state)

    def test_out_of_order_rejected(self):
        closes={s:list(range(1,202)) for s in SYMBOLS}
        state,_,_=process_closed_candle(initial_state(),86400000*300,closes,self.p,86400000*300)
        with self.assertRaises(ValueError):
            process_closed_candle(state,86400000*299,closes,self.p,86400000*300)

    def test_observation_before_close_rejected(self):
        closes={s:list(range(1,202)) for s in SYMBOLS}
        with self.assertRaises(ValueError):
            process_closed_candle(initial_state(),86400000*300,closes,self.p,86400000*300-1)

    def test_missing_symbol_rejected_without_mutation(self):
        state=initial_state()
        with self.assertRaises(ValueError):
            process_closed_candle(state,86400000*300,{"BTCUSDT":list(range(1,202))},self.p,86400000*300)
        self.assertIsNone(state["last_candle_ms"])
if __name__=="__main__": unittest.main()
