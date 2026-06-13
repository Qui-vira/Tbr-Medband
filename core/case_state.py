"""Persistent idempotency and workflow state for Band cases."""
from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"

TRACKED_STAGES = frozenset(
    {
        "CASE_OPENED",
        "INTAKE_REQUEST",
        "INTAKE_COMPLETE",
        "INTAKE_INCOMPLETE",
        "VERIFY_REQUEST",
        "CASE_CLEAR",
        "CASE_CAUTION",
        "CASE_ESCALATE",
        "RESOURCE_REQUEST",
        "RESOURCE_COMPLETE",
        "CASE_READY",
        "HUMAN_ALERT",
    }
)

TERMINAL_STAGES = frozenset({"CASE_READY", "HUMAN_ALERT", "CASE_REJECTED", "CASE_APPROVED"})

VERIFICATION_OUTCOMES = frozenset({"CASE_CLEAR", "CASE_CAUTION", "CASE_ESCALATE"})

_lock = threading.Lock()


def _case_path(case_id: str) -> Path:
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    return CASES_DIR / f"{case_id}.json"


def _load_raw(case_id: str) -> dict[str, Any]:
    path = _case_path(case_id)
    if not path.exists():
        return {"case_id": case_id}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read case state for %s: %s", case_id, exc)
        return {"case_id": case_id}


def _save_raw(case_id: str, data: dict[str, Any]) -> None:
    path = _case_path(case_id)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get_case_state(case_id: str) -> dict[str, Any]:
    with _lock:
        return _load_raw(case_id)


def completed_stages(case_id: str) -> set[str]:
    state = get_case_state(case_id)
    stages = state.get("completed_stages", [])
    return set(stages) if isinstance(stages, list) else set()


def stage_completed(case_id: str, stage: str) -> bool:
    return stage in completed_stages(case_id)


def is_terminal(case_id: str) -> bool:
    return bool(completed_stages(case_id) & TERMINAL_STAGES)


def get_verification_status(case_id: str) -> str | None:
    state = get_case_state(case_id)
    verification = state.get("verification") or {}
    if isinstance(verification, dict):
        status = verification.get("status")
        if isinstance(status, str):
            return status
    for stage in ("CASE_ESCALATE", "CASE_CAUTION", "CASE_CLEAR"):
        if stage_completed(case_id, stage):
            return stage
    return state.get("verification_status")


def record_stage(
    case_id: str,
    stage: str,
    *,
    payload: dict[str, Any] | None = None,
    room_id: str | None = None,
) -> None:
    if not case_id or not stage:
        return
    with _lock:
        data = _load_raw(case_id)
        stages = data.setdefault("completed_stages", [])
        if not isinstance(stages, list):
            stages = []
            data["completed_stages"] = stages
        if stage not in stages:
            stages.append(stage)
        data["case_id"] = case_id
        data["last_stage"] = stage
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if room_id:
            data["band_room_id"] = room_id
        if payload:
            if stage == "INTAKE_COMPLETE" or stage == "INTAKE_INCOMPLETE":
                data["intake"] = payload
            elif stage in VERIFICATION_OUTCOMES:
                data["verification"] = payload
                data["verification_status"] = stage
            elif stage == "RESOURCE_COMPLETE":
                data["resource"] = payload
            elif stage == "CASE_OPENED":
                data.setdefault("opened", payload)
            elif stage == "CASE_READY":
                data["status"] = "CASE_READY"
                data["summary"] = payload
        _save_raw(case_id, data)
        logger.info("Recorded stage %s for case %s", stage, case_id)


def extract_case_id(text: str) -> str | None:
    if not text:
        return None
    parsed = try_parse_json_payload(text)
    if parsed:
        case_id = parsed.get("case_id")
        if isinstance(case_id, str) and case_id.strip():
            return case_id.strip().upper()
    for pattern in (
        r'"case_id"\s*:\s*"([^"]+)"',
        r"Case ID:\s*([A-Z0-9-]+)",
        r"case_id[=:\s]+([A-Z0-9-]+)",
        r"MEDBAND-[A-Z0-9-]+",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1 if match.lastindex else 0).upper()
    return None


def try_parse_json_payload(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    if not (cleaned.startswith("{") and cleaned.endswith("}")):
        brace = cleaned.find("{")
        if brace >= 0:
            end = cleaned.rfind("}")
            if end > brace:
                cleaned = cleaned[brace : end + 1]
            else:
                return None
        else:
            return None
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def detect_stage(text: str, payload: dict[str, Any] | None = None) -> str | None:
    if payload and isinstance(payload.get("status"), str):
        status = payload["status"].upper()
        if status in TRACKED_STAGES:
            return status
    upper = text.upper()
    formatted_aliases = {
        "INTAKE COMPLETE": "INTAKE_COMPLETE",
        "CASE CLEAR": "CASE_CLEAR",
        "VERIFICATION CAUTION": "CASE_CAUTION",
        "VERIFICATION ESCALATION": "CASE_ESCALATE",
        "RESOURCE COMPLETE": "RESOURCE_COMPLETE",
        "CASE READY FOR HUMAN REVIEW": "CASE_READY",
        "CASE OPENED": "CASE_OPENED",
        "HUMAN ALERT": "HUMAN_ALERT",
    }
    for label, stage in formatted_aliases.items():
        if label in upper:
            return stage
    for stage in sorted(TRACKED_STAGES, key=len, reverse=True):
        if stage in upper:
            return stage
    if "@MEDLABBYTBR/INTAKE" in upper or "INTAKE_REQUEST" in upper:
        return "INTAKE_REQUEST"
    if "@MEDLABBYTBR/VERIFICATION" in upper and ("VERIFY" in upper or "PLEASE VERIFY" in upper):
        return "VERIFY_REQUEST"
    if "@MEDLABBYTBR/RESOURCE" in upper and ("RESOURCE" in upper or "AVAILABILITY" in upper):
        return "RESOURCE_REQUEST"
    return None
