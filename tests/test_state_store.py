import json
import tempfile
import unittest
from pathlib import Path
from simulator import initial_state
from state_store import initialize_state, load_state, save_state

class StateStoreTests(unittest.TestCase):
    def test_explicit_initialization_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            with self.assertRaises(FileNotFoundError):
                load_state(path)
            original=initialize_state(path)
            self.assertEqual(load_state(path),original)
            with self.assertRaises(FileExistsError):
                initialize_state(path)
    def test_atomic_save_and_reload(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            state=initialize_state(path)
            state["cash"]="9000"
            save_state(path,state)
            self.assertEqual(load_state(path)["cash"],"9000")
    def test_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            path.write_text("{broken",encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_state(path)
    def test_invalid_negative_cash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            state=initial_state()
            state["cash"]="-1"
            with self.assertRaises(ValueError):
                save_state(Path(d)/"state.json",state)
    def test_schema_version_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            path.write_text(json.dumps({"schema_version":999,"portfolio":initial_state()}))
            with self.assertRaises(ValueError):
                load_state(path)
if __name__=="__main__":
    unittest.main()
