import unittest
from test_daily_sequence import market,DAY
from simulator import initial_state
from paper_run import run
from datetime import datetime,timezone
class RecoveryTests(unittest.TestCase):
 def call(self,date):
  state=initial_state();state['last_candle_ms']=DAY*300;writes=[]
  result=run('owner/repo','token',commit=True,resume_gap=date,market_loader=lambda:market(303),state_loader=lambda *_:(state,'sha'),state_writer=lambda *a:writes.append(a))
  return state,writes,result
 def test_resume_records_gap_without_backfill(self):
  date=datetime.fromtimestamp(DAY*303/1000,timezone.utc).date().isoformat()
  old,writes,result=self.call(date);saved=writes[0][2]
  self.assertEqual(len(saved['history']),1)
  self.assertEqual(len(saved['reconciliations'][0]['missing_session_dates_utc']),2)
  self.assertEqual(old['last_candle_ms'],DAY*300)
  self.assertEqual(saved['last_candle_ms'],DAY*303)
 def test_wrong_date_blocked(self):
  with self.assertRaises(ValueError):self.call('2026-01-01')
 def test_no_authorization_blocked(self):
  with self.assertRaises(ValueError):self.call(None)
