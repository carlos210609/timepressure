import tempfile, unittest
from timepressure.models import PressureState
from timepressure.models import State
from timepressure.store import Store
from timepressure.orchestrator import Orchestrator

class OrchestratorTests(unittest.TestCase):
    def test_action_guard_and_learning(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(tmp); state=s.init(100,60000); o=Orchestrator(state,s)
            with self.assertRaises(PermissionError):
                o.validate_action("bypass CAPTCHA")
            class T:
                marketplace="test"; task_id="1"; category="coding"
            o.learn(T(),True,250,15)
            self.assertEqual(state.learning["test:coding"]["successes"],1)
            self.assertEqual(state.executions, [])
