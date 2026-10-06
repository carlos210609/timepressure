from __future__ import annotations
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import time

DEFAULT_STATE = Path(".timepressure.json")

@dataclass
class State:
    target_url: str = ""
    pressure: float = 50.0
    cycles: int = 0
    verified_visits: int = 0
    last_action: str = ""
    last_title: str = ""
    updated_at: float = field(default_factory=time)

    def save(self, path: Path = DEFAULT_STATE) -> None:
        self.updated_at = time()
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = DEFAULT_STATE) -> "State":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})
        except (OSError, ValueError, TypeError):
            return cls()
