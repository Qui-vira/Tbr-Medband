"""Tests for Band message guards and formatting."""
import json
from datetime import datetime, timezone

import pytest
from band.core.types import PlatformMessage

from core.band_messaging import (
    evaluate_outbound,
    extract_recipient,
    format_case_opened,
    is_visible_json,
    should_skip_inbound,
    strip_em_dash,
)
from core.case_state import init_case_state, record_stage


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("MEDBAND_DATA_DIR", str(tmp_path))
    import core.case_store as store

    store.DATA_DIR = tmp_path
    store.SQLITE_PATH = tmp_path / "medband_state.db"
    store._pg_pool = None
    init_case_state()


def _msg(content: str, sender: str = "Coordinator") -> PlatformMessage:
    return PlatformMessage(
        id="m1",
        room_id="room1",
        content=content,
        sender_id="s1",
        sender_type="Agent",
        sender_name=sender,
        message_type="text",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )


def test_strip_em_dash():
    assert strip_em_dash("hello — world") == "hello - world"


def test_format_case_opened():
    text = format_case_opened(
        {
            "requester_name": "Ada Okonkwo",
            "institution_name": "Demo Institution",
            "requested_service": "Amoxicillin 500mg",
            "presenting_issue": "Throat infection",
            "urgency": "medium",
            "prescription_code": "TBR-DOC-0042",
        }
    )
    assert "📋 CASE OPENED" in text
    assert "Ada Okonkwo" in text
    assert "—" not in text


def test_duplicate_stage_blocked():
    from core.case_state import try_claim_outbound

    case_id = "TEST1234"
    assert try_claim_outbound(case_id, "CASE_OPENED", "coordinator", "room")
    raw = json.dumps({"status": "CASE_OPENED", "case_id": case_id})
    decision = evaluate_outbound("coordinator", raw, room_id="room1")
    assert decision.skip is True
    assert decision.reason == "duplicate_stage"


def test_false_human_alert_blocked():
    case_id = "TEST5678"
    record_stage(case_id, "CASE_CLEAR", payload={"status": "CASE_CLEAR", "case_id": case_id})
    raw = json.dumps({"status": "HUMAN_ALERT", "case_id": case_id, "reason": "oops"})
    decision = evaluate_outbound("coordinator", raw, room_id="room1")
    assert decision.skip is True
    assert decision.reason == "false_human_alert"


def test_intake_ignores_non_coordinator():
    skip, reason = should_skip_inbound(
        "intake",
        _msg("please process", sender="Verification"),
        case_id="ABC123",
    )
    assert skip is True
    assert reason == "wrong_recipient"


def test_json_replaced_with_formatted_message():
    payload = {
        "status": "INTAKE_COMPLETE",
        "case_id": "NEWCASE1",
        "requester_name": "Ada Okonkwo",
        "requested_service": "Amoxicillin 500mg",
        "presenting_issue": "Throat infection",
        "urgency": "medium",
    }
    decision = evaluate_outbound("intake", json.dumps(payload), room_id="room1")
    assert decision.skip is False
    assert decision.formatted_content is not None
    assert "INTAKE COMPLETE" in decision.formatted_content
    assert is_visible_json(json.dumps(payload)) is True


def test_extract_recipient_from_mentions():
    recipient = extract_recipient(
        {"content": "verify this", "mentions": ["@medlabbytbr/verification"]}
    )
    assert recipient == "verification"


def test_coordinator_processes_intake_complete_after_intake_recorded():
    case_id = "MB-TEST001"
    record_stage(
        case_id,
        "INTAKE_COMPLETE",
        payload={
            "status": "INTAKE_COMPLETE",
            "case_id": case_id,
            "requester_name": "Ada Okonkwo",
            "requested_service": "Amoxicillin 500mg",
        },
    )
    msg = _msg("📋 INTAKE COMPLETE\n\nPatient: Ada Okonkwo", sender="Intake")
    skip, reason = should_skip_inbound("coordinator", msg, case_id=case_id)
    assert skip is False


def test_coordinator_skips_intake_complete_after_verify_request():
    case_id = "MB-TEST002"
    record_stage(case_id, "INTAKE_COMPLETE", payload={"case_id": case_id})
    record_stage(case_id, "VERIFY_REQUEST", payload={"case_id": case_id})
    msg = _msg("📋 INTAKE COMPLETE\n\nPatient: Ada", sender="Intake")
    skip, reason = should_skip_inbound("coordinator", msg, case_id=case_id)
    assert skip is True
    assert reason == "duplicate_stage"


def test_intake_complete_includes_case_id():
    text = format_case_opened(
        {"case_id": "MB-ABC12345", "requester_name": "Ada", "requested_service": "Amox"}
    )
    assert "Case ID: MB-ABC12345" in text
