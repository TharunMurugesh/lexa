import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('{"cases":[],"verdicts":[],"agent_logs":[]}', encoding="utf-8")

    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_case(self, title: str, text: str, file_path: str | None = None) -> str:
        data = self._read()
        case_id = str(uuid4())
        data["cases"].append(
            {"id": case_id, "title": title, "file_path": file_path, "raw_text": text, "status": "pending", "created_at": _now()}
        )
        self._write(data)
        return case_id

    def update_case_status(self, case_id: str, status: str) -> None:
        data = self._read()
        for case in data["cases"]:
            if case["id"] == case_id:
                case["status"] = status
        self._write(data)

    def get_case(self, case_id: str) -> dict | None:
        data = self._read()
        return next((case for case in data["cases"] if case["id"] == case_id), None)

    def list_cases(self) -> list[dict]:
        data = self._read()
        verdict_by_case = {verdict["case_id"]: verdict for verdict in data["verdicts"]}
        return [{**case, "verdict": verdict_by_case.get(case["id"])} for case in reversed(data["cases"])]

    def save_verdict(self, case_id: str, state: dict) -> str:
        data = self._read()
        verdict_id = str(uuid4())
        jury = state.get("jury_vote", {})
        record = {
            "id": verdict_id,
            "case_id": case_id,
            "verdict": state.get("final_verdict", "Insufficient Evidence"),
            "confidence": jury.get("confidence", 0),
            "evidence_summary": json.dumps(state.get("evidence", {})),
            "prosecution_args": state.get("prosecution", ""),
            "defense_args": state.get("defense", ""),
            "contradictions": state.get("contradictions", []),
            "retrieved_laws": state.get("retrieved_laws", []),
            "judge_reasoning": state.get("judge_reasoning", ""),
            "jury_vote": jury,
            "appeal_decision": state.get("appeal_decision", ""),
            "agent_trace": state.get("agent_trace", []),
            "created_at": _now(),
        }
        data["verdicts"] = [item for item in data["verdicts"] if item["case_id"] != case_id]
        data["verdicts"].append(record)
        self._write(data)
        return verdict_id

    def get_verdict(self, case_id: str) -> dict | None:
        data = self._read()
        return next((verdict for verdict in reversed(data["verdicts"]) if verdict["case_id"] == case_id), None)

    def log_agent(self, case_id: str, agent_name: str, output: object) -> None:
        data = self._read()
        data["agent_logs"].append({"id": str(uuid4()), "case_id": case_id, "agent_name": agent_name, "output": output, "created_at": _now()})
        self._write(data)

    def get_logs(self, case_id: str) -> list[dict]:
        data = self._read()
        return [log for log in data["agent_logs"] if log["case_id"] == case_id]


store = LocalStore(settings.local_store)


def save_case(title: str, text: str, file_path: str | None = None) -> str:
    return store.save_case(title, text, file_path)


def update_case_status(case_id: str, status: str) -> None:
    store.update_case_status(case_id, status)


def get_case(case_id: str) -> dict | None:
    return store.get_case(case_id)


def list_cases() -> list[dict]:
    return store.list_cases()


def save_verdict(case_id: str, state: dict) -> str:
    return store.save_verdict(case_id, state)


def get_verdict(case_id: str) -> dict | None:
    return store.get_verdict(case_id)


def log_agent(case_id: str, agent_name: str, output: object) -> None:
    store.log_agent(case_id, agent_name, output)


def get_logs(case_id: str) -> list[dict]:
    return store.get_logs(case_id)
