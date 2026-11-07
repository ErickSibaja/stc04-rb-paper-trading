import unittest
from decimal import Decimal
from market_data import validate_daily_klines, DAY_MS
from simulator import initial_state,rebalance,signal

class NonFiniteSafetyTests(unittest.TestCase):
    def rows(self,close):
        start=1000
        return [[(start+i)*DAY_MS,"1","1","1",close,"1",(start+i+1)*DAY_MS-1]
                for i in range(201)]
    def test_daily_nan_rejected(self):
        with self.assertRaises(ValueError):
            validate_daily_klines(self.rows("NaN"),1201*DAY_MS+60000)
    def test_daily_infinity_rejected(self):
        with self.assertRaises(ValueError):
            validate_daily_klines(self.rows("Infinity"),1201*DAY_MS+60000)
    def test_signal_nan_rejected(self):
        with self.assertRaises(ValueError):
            signal(["1"]*199+["NaN"])
    def test_quote_infinity_rejected(self):
        state=initial_state()
        prices={"BTCUSDT":Decimal("Infinity"),"ETHUSDT":Decimal("2500")}
        signals={s:{"eligible":True} for s in prices}
        with self.assertRaises(ValueError):
            rebalance(state,prices,signals,"test")
        self.assertEqual(state,initial_state())
if __name__=="__main__": unittest.main()
