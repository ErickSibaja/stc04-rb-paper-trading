import unittest
from decimal import Decimal as D
from simulator import signal, initial_state, rebalance, equity, SYMBOLS

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
if __name__=="__main__": unittest.main()
