import tempfile, unittest
from timepressure.risk_engine import RiskEngine
from timepressure.wallet_engine import WalletEngine
from timepressure.arbitrage import ArbitrageAnalyzer
from timepressure.bug_bounty import ScopeValidator, ProgramRanker

class FinancialEngineTests(unittest.TestCase):
    def test_arbitrage_negative_is_rejected(self):
        op=ArbitrageAnalyzer().analyze({"source":"a","asset":"BTC","price":100},{"source":"b","asset":"BTC","price":99},100,fees=2)
        self.assertLessEqual(op.net_profit,0)
        self.assertEqual(op.status,"REJECTED")

    def test_old_risk_limit_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            r=RiskEngine(d); r.set_limit("max_trade_amount",10)
            x=r.check(capital_available=100,trade_amount=11,expected_profit=2,roi=.2)
            self.assertEqual(x.decision,"BLOCK")

    def test_live_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            r=RiskEngine(d)
            self.assertFalse(r.snapshot()["live_mode"])
            self.assertEqual(r.check(capital_available=100,trade_amount=1,expected_profit=2,roi=.2).decision,"APPROVE")

    def test_emergency_stop_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            r=RiskEngine(d); r.emergency_stop()
            self.assertEqual(r.check(capital_available=100,trade_amount=1,expected_profit=2,roi=.2).decision,"BLOCK")

    def test_wallet_ledger_and_reserve_protection(self):
        with tempfile.TemporaryDirectory() as d:
            w=WalletEngine(d); w.allocate_revenue(100,"task","ref-1")
            self.assertTrue(w.verify_ledger())
            self.assertAlmostEqual(w.data["balances"]["RESERVED"],70)
            with self.assertRaises(PermissionError): w.debit("RESERVED",1,"test")

    def test_bounty_scope(self):
        v=ScopeValidator()
        ok,_=v.validate({"scope":["example.com"],"rules_confirmed":True,"automation_allowed":True},"other.com",True)
        self.assertFalse(ok)
        ok,_=v.validate({"scope":["example.com"],"rules_confirmed":True,"automation_allowed":True},"example.com",True)
        self.assertTrue(ok)

    def test_bounty_rank_uses_expected_value_per_hour(self):
        r=ProgramRanker().rank([{"id":"a","max_reward":100,"estimated_hours":1,"finding_probability":.5,"risk":0},
                                {"id":"b","max_reward":500,"estimated_hours":20,"finding_probability":.1,"risk":0}])
        self.assertEqual(r[0]["id"],"a")

if __name__=="__main__": unittest.main()
