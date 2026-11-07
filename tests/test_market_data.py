import unittest
from market_data import DAY_MS, validate_daily_klines

class TestBinanceDailyValidation(unittest.TestCase):
    def rows(self, n=201, start=1000):
        return [[(start+i)*DAY_MS,"1","1","1","100","1",(start+i+1)*DAY_MS-1] for i in range(n)]
    def test_valid_completed_series(self):
        r=self.rows()
        result=validate_daily_klines(r,(1201)*DAY_MS+60000)
        self.assertEqual(len(result["closes"]),201)
        self.assertEqual(result["candle_ms"],1201*DAY_MS)
    def test_rejects_incomplete(self):
        r=self.rows()
        with self.assertRaises(ValueError):
            validate_daily_klines(r,1200*DAY_MS)
    def test_rejects_gap(self):
        r=self.rows()
        r[100][0]+=DAY_MS
        r[100][6]+=DAY_MS
        with self.assertRaises(ValueError):
            validate_daily_klines(r,1201*DAY_MS+60000)
    def test_rejects_stale(self):
        r=self.rows()
        with self.assertRaises(ValueError):
            validate_daily_klines(r,1203*DAY_MS+60000)
    def test_rejects_insufficient(self):
        with self.assertRaises(ValueError):
            validate_daily_klines(self.rows(199),1201*DAY_MS+60000)

if __name__=="__main__":
    unittest.main()
