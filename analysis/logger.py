import json
import sys
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Logger:
    label: str
    path: Path | None = None

    def __post_init__(self):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(str(self.path), 'w')
        else:
            self._file = sys.stdout

    def log(self, tick: int, event: str, *, epoch: int | None = None, **kwargs) -> None:
        entry = {"tick": tick, "label": self.label, "event": event, **kwargs}
        if epoch is not None:
            entry["epoch"] = epoch

        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def close(self) -> None:
        if self._file is not sys.stdout:
            self._file.close()