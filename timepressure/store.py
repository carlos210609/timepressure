import json
import os
import tempfile
import time
from pathlib import Path

from .models import PressureState, State


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.file = self.directory / "state.json"

    def init(self, target_cents, cycle_ms):
        self.directory.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.directory, 0o700)
        except OSError:
            pass
        if self.file.exists():
            try:
                return State.from_dict(json.loads(self.file.read_text()))
            except (OSError, ValueError, KeyError, TypeError):
                pass
        now = time.time()
        state = State(
            1,
            now,
            PressureState(now, target_cents, 0, 0, "alive", now + cycle_ms),
        )
        self.save(state)
        return state

    def save(self, state):
        self.directory.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.directory, 0o700)
        except OSError:
            pass
        fd, tmp = tempfile.mkstemp(prefix="state-", suffix=".json", dir=self.directory)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(state.to_dict(), handle, indent=2)
            os.replace(tmp, self.file)
            try:
                os.chmod(self.file, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def add_memory(self, state, event):
        state.memory.append(event)
        state.memory = state.memory[-5000:]
        self.save(state)

    def add_revenue(self, state, event):
        state.revenue.append(event)
        self.save(state)
