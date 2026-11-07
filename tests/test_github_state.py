import base64
import io
import json
import unittest
from simulator import initial_state
from github_state import load_remote_state, save_remote_state

class FakeResponse:
    def __init__(self,body): self.body=body
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,*args): return json.dumps(self.body).encode()
class RemoteStateTests(unittest.TestCase):
    def test_read_with_sha(self):
        doc={"schema_version":1,"portfolio":initial_state()}
        content=base64.b64encode(json.dumps(doc).encode()).decode()
        def opener(req,timeout):
            self.assertIn("ref=paper-state",req.full_url)
            return FakeResponse({"encoding":"base64","sha":"knownsha","content":content})
        state,sha=load_remote_state("owner/repo","dummy-token",opener)
        self.assertEqual(sha,"knownsha")
        self.assertEqual(state["cash"],"10000")
    def test_update_has_expected_sha_and_isolated_branch(self):
        def opener(req,timeout):
            self.assertEqual(req.get_method(),"PUT")
            data=json.loads(req.data)
            self.assertEqual(data["sha"],"oldsha")
            self.assertEqual(data["branch"],"paper-state")
            self.assertEqual(json.loads(base64.b64decode(data["content"]))["portfolio"]["cash"],"10000")
            return FakeResponse({"content":{"sha":"newsha"}})
        save_remote_state("owner/repo","dummy-token",initial_state(),"oldsha",opener)
    def test_refuse_write_without_sha(self):
        with self.assertRaises(ValueError):
            save_remote_state("owner/repo","dummy-token",initial_state(),None)
    def test_refuse_missing_token(self):
        with self.assertRaises(ValueError):
            load_remote_state("owner/repo","")
if __name__=="__main__": unittest.main()
