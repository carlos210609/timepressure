import unittest
from timepressure.control_plane import Execution,TaskStatus,SafetyPolicy,VerifiedLedger,learning_update

class ControlPlaneTests(unittest.TestCase):
    def test_lifecycle(self):
        e=Execution("1","market","task"); e.transition(TaskStatus.RUNNING); e.transition(TaskStatus.VERIFYING); e.transition(TaskStatus.SUBMITTED); e.transition(TaskStatus.VERIFIED)
        self.assertEqual(e.status,"verified")
    def test_ledger_requires_reference_and_dedupes(self):
        l=VerifiedLedger(); x=l.add_verified("e",100,"tx"); self.assertIsNotNone(x); self.assertIsNone(l.add_verified("e",100,"tx")); self.assertEqual(l.snapshot()["verifiedRevenueCents"],100)
    def test_safety(self):
        with self.assertRaises(PermissionError): SafetyPolicy().validate({"instruction":"bypass CAPTCHA"})
    def test_learning(self):
        row=learning_update({},"M","coding",True,100,10); self.assertEqual(row["successRate"],1.0)
