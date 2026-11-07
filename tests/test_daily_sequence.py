import unittest
from simulator import initial_state
from paper_run import run

DAY=86400000
SYMBOLS=("BTCUSDT","ETHUSDT")

def market(day):
    t=DAY*day
    return {"host":"fixture","candle_ms":t,"observed_at_ms":t+1000,
            "closes":{s:list(range(1,202)) for s in SYMBOLS},
            "quotes":{"BTCUSDT":"50000","ETHUSDT":"2500"}}

class DailySequenceTests(unittest.TestCase):
    def test_one_day_later_can_commit(self):
        state=initial_state()
        state["last_candle_ms"]=DAY*300
        writes=[]
        result=run("owner/repo","token",commit=True,
            market_loader=lambda:market(301),
            state_loader=lambda *_:(state,"sha"),
            state_writer=lambda *args:writes.append(args))
        self.assertTrue(result["committed"])
        self.assertEqual(writes[0][2]["last_candle_ms"],DAY*301)
    def test_two_day_gap_fails_closed(self):
        state=initial_state()
        state["last_candle_ms"]=DAY*300
        writes=[]
        with self.assertRaisesRegex(ValueError,"Gap in daily"):
            run("owner/repo","token",commit=True,
                market_loader=lambda:market(302),
                state_loader=lambda *_:(state,"sha"),
                state_writer=lambda *args:writes.append(args))
        self.assertEqual(writes,[])
    def test_initial_first_day_allowed(self):
        writes=[]
        result=run("owner/repo","token",commit=True,
            market_loader=lambda:market(300),
            state_loader=lambda *_:(initial_state(),"sha"),
            state_writer=lambda *args:writes.append(args))
        self.assertTrue(result["committed"])
        self.assertEqual(len(writes),1)

if __name__=="__main__": unittest.main()
