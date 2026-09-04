import json
import os
from datetime import datetime, timezone


class FixerLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self._session = None
        self._sequence = 0

    def start_session(self, csv_path: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._session = {
            "session_id": now,
            "started_at": now,
            "completed_at": None,
            "csv_path": csv_path,
            "summary": {"total_tool_calls": 0, "findings_count": None},
            "tool_calls": [],
        }
        self._sequence = 0
        self._flush()

    def log_tool_call(
        self,
        tool_name: str,
        input_args: dict,
        output: str,
        status: str,
        called_at: str,
        completed_at: str,
        duration_ms: int,
    ) -> None:
        self._sequence += 1
        self._session["tool_calls"].append({
            "sequence": self._sequence,
            "tool_name": tool_name,
            "called_at": called_at,
            "completed_at": completed_at,
            "duration_ms": duration_ms,
            "status": status,
            "input": input_args,
            "output": output,
        })
        self._session["summary"]["total_tool_calls"] = self._sequence
        self._flush()

    def end_session(self, findings_count: int | None = None) -> None:
        self._session["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._session["summary"]["findings_count"] = findings_count
        self._flush()

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        sessions = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path) as f:
                    sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                sessions = []
        if sessions and sessions[-1]["session_id"] == self._session["session_id"]:
            sessions[-1] = self._session
        else:
            sessions.append(self._session)
        with open(self.log_path, "w") as f:
            json.dump(sessions, f, indent=2)
