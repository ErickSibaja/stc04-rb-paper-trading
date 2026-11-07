import json
import unittest
from urllib.error import HTTPError
from simulator import initial_state
from github_state import save_remote_state
from paper_run import run

class ConflictSafetyTests(unittest.TestCase):
    def test_remote_sha_conflict_fails_without_retry(self):
        calls=[]
        def opener(request,timeout):
            calls.append(request)
            raise HTTPError(request.full_url,409,"Conflict",{},None)
        with self.assertRaises(HTTPError) as raised:
            save_remote_state("owner/repo","test-token",initial_state(),"outdated-sha",opener)
        self.assertEqual(raised.exception.code,409)
        self.assertEqual(len(calls),1)

    def test_failed_write_is_not_reported_committed(self):
        t=86400000*300
        market={"host":"fixture","candle_ms":t,"observed_at_ms":t+1000,
                "closes":{s:list(range(1,202)) for s in ("BTCUSDT","ETHUSDT")},
                "quotes":{"BTCUSDT":"50000","ETHUSDT":"2500"}}
        def loader(repo,token):
            return initial_state(),"sha1"
        def conflict_writer(*args):
            raise RuntimeError("conflicting state revision")
        with self.assertRaisesRegex(RuntimeError,"conflicting"):
            run("owner/repo","token",commit=True,market_loader=lambda:market,
                state_loader=loader,state_writer=conflict_writer)

    def test_stale_candle_never_writes(self):
        t=86400000*300
        market={"host":"fixture","candle_ms":t,"observed_at_ms":t+1000,
                "closes":{s:list(range(1,202)) for s in ("BTCUSDT","ETHUSDT")},
                "quotes":{"BTCUSDT":"50000","ETHUSDT":"2500"}}
        def loader(repo,token):
            state=initial_state()
            state["last_candle_ms"]=t+86400000
            return state,"sha1"
        writes=[]
        with self.assertRaises(ValueError):
            run("owner/repo","token",commit=True,market_loader=lambda:market,
                state_loader=loader,state_writer=lambda *a:writes.append(a))
        self.assertFalse(writes)

if __name__=="__main__": unittest.main()
