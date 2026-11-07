import unittest
from simulator import initial_state
from paper_run import run

class PaperRunTests(unittest.TestCase):
    def setUp(self):
        t=86400000*300
        self.market={"host":"fixture","candle_ms":t,"observed_at_ms":t+60000,
                     "closes":{s:list(range(1,202)) for s in ("BTCUSDT","ETHUSDT")},
                     "quotes":{"BTCUSDT":"50000","ETHUSDT":"2500"}}
        self.writes=[]
    def loader(self,repo,token):
        return initial_state(),"sha-old"
    def writer(self,*args):
        self.writes.append(args)
    def test_default_does_not_write(self):
        result=run("owner/repo","token",market_loader=lambda:self.market,
                   state_loader=self.loader,state_writer=self.writer)
        self.assertFalse(result["committed"])
        self.assertEqual(self.writes,[])
    def test_explicit_commit_writes_once(self):
        result=run("owner/repo","token",commit=True,market_loader=lambda:self.market,
                   state_loader=self.loader,state_writer=self.writer)
        self.assertTrue(result["committed"])
        self.assertEqual(len(self.writes),1)
        self.assertEqual(self.writes[0][3],"sha-old")
        self.assertEqual(self.writes[0][2]["last_candle_ms"],self.market["candle_ms"])
    def test_duplicate_commit_is_noop(self):
        def loaded(repo,token):
            state=initial_state()
            state["last_candle_ms"]=self.market["candle_ms"]
            return state,"sha-old"
        result=run("owner/repo","token",commit=True,market_loader=lambda:self.market,
                   state_loader=loaded,state_writer=self.writer)
        self.assertFalse(result["committed"])
        self.assertEqual(self.writes,[])
if __name__=="__main__": unittest.main()
