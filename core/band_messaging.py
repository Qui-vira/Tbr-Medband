"""Band message routing guards, idempotency, and human-readable formatting."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from band.core.types import PlatformMessage

from core.case_state import (
    TRACKED_STAGES,
    detect_stage,
    extract_case_id,
    get_case_state,
    get_verification_status,
    is_terminal,
    record_stage,
    stage_completed,
    try_parse_json_payload,
)

logger = logging.getLogger(__name__)

SEND_MESSAGE_TOOLS = frozenset({"band_send_message", "thenvoi_send_message"})

AGENT_ALIASES = {
    "coordinator": {"coordinator", "medlabbytbr/coordinator", "@medlabbytbr/coordinator"},
    "intake": {"intake", "medlabbytbr/intake", "@medlabbytbr/intake"},
    "verification": {
        "verification",
        "medlabbytbr/verification",
        "@medlabbytbr/verification",
    },
    "resource": {"resource", "medlabbytbr/resource", "@medlabbytbr/resource"},
}

ROUTING_ONLY_STAGES = frozenset({"VERIFY_REQUEST", "RESOURCE_REQUEST", "INTAKE_REQUEST"})

AGENT_REPLY_STAGES = frozenset(
    {
        "INTAKE_COMPLETE",
        "CASE_CLEAR",
        "CASE_CAUTION",
        "CASE_ESCALATE",
        "RESOURCE_COMPLETE",
    }
)


@dataclass
class OutboundDecision:
    skip: bool = False
    reason: str = ""
    formatted_content: str | None = None
    stage: str | None = None
    case_id: str | None = None
    record_on_success: bool = True


def strip_em_dash(text: str) -> str:
    return text.replace("\u2014", "-").replace("\u2013", "-")


def normalize_sender(name: str | None) -> str:
    if not name:
        return ""
    return name.strip().lower().replace("@", "")


def is_self_sender(sender: str, agent_role: str) -> bool:
    normalized = normalize_sender(sender)
    aliases = AGENT_ALIASES.get(agent_role, {agent_role})
    return normalized in {a.lower().replace("@", "") for a in aliases}


def is_coordinator_sender(sender: str) -> bool:
    normalized = normalize_sender(sender)
    return normalized in {a.lower().replace("@", "") for a in AGENT_ALIASES["coordinator"]}


def is_agent_sender(sender: str, role: str) -> bool:
    normalized = normalize_sender(sender)
    return normalized in {a.lower().replace("@", "") for a in AGENT_ALIASES.get(role, set())}


def _title(value: str) -> str:
    if not value:
        return "Unknown"
    return value.strip().title()


def _pick(data: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return default


def format_case_opened(payload: dict[str, Any]) -> str:
    intake = payload.get("intake") if isinstance(payload.get("intake"), dict) else {}
    patient = _pick(payload, "requester_name", "patient_name") or _pick(intake, "requester_name", "patient_name")
    institution = _pick(payload, "institution_name") or _pick(intake, "institution_name") or "Demo Institution"
    request = _pick(payload, "requested_service", "raw_input") or _pick(intake, "requested_service")
    issue = _pick(payload, "presenting_issue") or _pick(intake, "presenting_issue")
    urgency = _title(_pick(payload, "urgency") or _pick(intake, "urgency") or "medium")
    rx = _pick(payload, "prescription_code") or _pick(intake, "prescription_code")

    lines = [
        "📋 CASE OPENED",
        "",
        f"Patient: {patient or 'Unknown'}",
        f"Institution: {institution}",
        f"Request: {request or 'Not specified'}",
        f"Issue: {issue or 'Not specified'}",
        f"Urgency: {urgency}",
    ]
    if rx:
        lines.append(f"Prescription Code: {rx}")
    lines.extend(
        [
            "",
            "Next Step:",
            "Intake agent will structure the request.",
        ]
    )
    return strip_em_dash("\n".join(lines))


def format_intake_complete(payload: dict[str, Any]) -> str:
    patient = _pick(payload, "requester_name")
    request = _pick(payload, "requested_service")
    issue = _pick(payload, "presenting_issue")
    urgency = _title(_pick(payload, "urgency") or "medium")
    rx = _pick(payload, "prescription_code")
    lines = [
        "📋 INTAKE COMPLETE",
        "",
        f"Patient: {patient or 'Unknown'}",
        f"Request: {request or 'Not specified'}",
        f"Issue: {issue or 'Not specified'}",
        f"Urgency: {urgency}",
    ]
    if rx:
        lines.append(f"Prescription Code: {rx}")
    lines.extend(
        [
            "",
            "Next Step:",
            "Coordinator will send this case to Verification.",
        ]
    )
    return strip_em_dash("\n".join(lines))


def format_verification(payload: dict[str, Any]) -> str:
    status = _pick(payload, "status", default="CASE_CLEAR").upper()
    drug = _pick(payload, "drug_name", "requested_service")
    reason = _pick(payload, "reason", "recommendation")
    if status == "CASE_ESCALATE":
        return strip_em_dash(
            "\n".join(
                [
                    "🚨 VERIFICATION ESCALATION",
                    "",
                    f"Request: {drug or 'Unknown'}",
                    f"Reason: {reason or 'Safety review required.'}",
                    "",
                    "Next Step:",
                    "Coordinator will alert a human approver.",
                ]
            )
        )
    if status == "CASE_CAUTION":
        return strip_em_dash(
            "\n".join(
                [
                    "🟡 VERIFICATION CAUTION",
                    "",
                    f"Request: {drug or 'Unknown'}",
                    f"Notes: {reason or 'Proceed with caution.'}",
                    "",
                    "Next Step:",
                    "Coordinator will check resource availability.",
                ]
            )
        )
    clear_line = f"{drug or 'This request'} is cleared to proceed."
    if reason and "clear" not in reason.lower():
        clear_line = reason
    return strip_em_dash(
        "\n".join(
            [
                "✅ VERIFICATION COMPLETE",
                "",
                "Verification:",
                clear_line,
                "No safety concern was found.",
                "",
                "Next Step:",
                "Coordinator will check resource availability.",
            ]
        )
    )


def format_resource_complete(payload: dict[str, Any]) -> str:
    name = _pick(payload, "drug_name", "requested_service", "test_name")
    institution = _pick(payload, "institution", "institution_name")
    in_stock = payload.get("in_stock", True)
    qty = payload.get("quantity_available")
    notes = _pick(payload, "notes")
    lines = ["📦 RESOURCE COMPLETE", ""]
    lines.append(f"Request: {name or 'Unknown'}")
    if institution:
        lines.append(f"Institution: {institution}")
    if in_stock:
        if qty is not None:
            lines.append(f"Availability: In stock with {qty} units available.")
        else:
            lines.append("Availability: In stock.")
    else:
        lines.append("Availability: Not currently in stock.")
    if notes:
        lines.append(f"Notes: {notes}")
    lines.extend(["", "Next Step:", "Coordinator will prepare the case summary."])
    return strip_em_dash("\n".join(lines))


def format_case_ready(payload: dict[str, Any], case_id: str) -> str:
    state = get_case_state(case_id)
    intake = payload.get("intake") if isinstance(payload.get("intake"), dict) else state.get("intake") or {}
    verification = (
        payload.get("verification")
        if isinstance(payload.get("verification"), dict)
        else state.get("verification") or {}
    )
    resource = (
        payload.get("resource") if isinstance(payload.get("resource"), dict) else state.get("resource") or {}
    )

    patient = _pick(intake, "requester_name") or _pick(payload, "requester_name", "patient_name")
    institution = _pick(intake, "institution_name") or _pick(payload, "institution_name") or "Demo Institution"
    request = _pick(intake, "requested_service") or _pick(payload, "requested_service")
    issue = _pick(intake, "presenting_issue")
    urgency = _title(_pick(intake, "urgency") or "medium")

    ver_status = _pick(verification, "status").upper()
    drug = _pick(verification, "drug_name") or request
    if ver_status == "CASE_CLEAR":
        verification_text = f"{drug or request or 'The request'} is cleared to proceed.\nNo safety concern was found."
    elif ver_status == "CASE_CAUTION":
        verification_text = _pick(verification, "reason") or "Proceed with caution."
    else:
        verification_text = _pick(verification, "reason") or "Verification completed."

    if resource.get("in_stock") is False:
        availability = _pick(resource, "notes") or "Not currently available."
    elif resource.get("quantity_available") is not None:
        availability = f"In stock with {resource.get('quantity_available')} units available."
    else:
        availability = _pick(resource, "notes") or "Availability confirmed."

    recommended = _pick(payload, "recommended_action") or "Dispense medication after human approval."

    return strip_em_dash(
        "\n".join(
            [
                "📋 CASE READY FOR HUMAN REVIEW",
                "",
                "Patient:",
                patient or "Unknown",
                "",
                "Institution:",
                institution,
                "",
                "Request:",
                request or "Not specified",
                "",
                "Issue:",
                issue or "Not specified",
                "",
                "Urgency:",
                urgency,
                "",
                "Verification:",
                verification_text,
                "",
                "Availability:",
                availability,
                "",
                "Recommended Action:",
                recommended,
                "",
                "Human Decision Required:",
                "To approve this case, type:",
                "",
                "APPROVE",
                "",
                "To reject this case, type:",
                "",
                "REJECT: [reason]",
                "",
                "Important:",
                "No AI has approved this case. Final approval must come from the pharmacist.",
            ]
        )
    )


def format_human_alert(payload: dict[str, Any]) -> str:
    reason = _pick(payload, "reason", "message") or "Human review required."
    patient = _pick(payload, "requester_name", "patient_name")
    request = _pick(payload, "requested_service")
    institution = _pick(payload, "institution_name") or "Demo Institution"
    return strip_em_dash(
        "\n".join(
            [
                "🚨 HUMAN ALERT",
                "",
                f"Patient: {patient or 'Unknown'}",
                f"Request: {request or 'Not specified'}",
                f"Institution: {institution}",
                "",
                f"Reason: {reason}",
                "",
                "Please respond with:",
                "APPROVE WITH OVERRIDE: [justification]",
                "REJECT: [reason]",
                "ESCALATE FURTHER: [who to contact]",
            ]
        )
    )


def format_stage_message(stage: str, payload: dict[str, Any], case_id: str) -> str:
    formatters = {
        "CASE_OPENED": format_case_opened,
        "INTAKE_COMPLETE": format_intake_complete,
        "CASE_CLEAR": format_verification,
        "CASE_CAUTION": format_verification,
        "CASE_ESCALATE": format_verification,
        "RESOURCE_COMPLETE": format_resource_complete,
        "CASE_READY": lambda p: format_case_ready(p, case_id),
        "HUMAN_ALERT": format_human_alert,
    }
    formatter = formatters.get(stage)
    if formatter:
        return formatter(payload)
    return strip_em_dash(json.dumps(payload, indent=2, default=str))


def is_visible_json(content: str) -> bool:
    payload = try_parse_json_payload(content)
    if payload and payload.get("status"):
        return True
    stripped = content.strip()
    return stripped.startswith("{") and '"status"' in stripped


def should_skip_inbound(
    agent_role: str,
    msg: PlatformMessage,
    *,
    case_id: str | None,
) -> tuple[bool, str]:
    sender = msg.sender_name or msg.sender_type or ""

    if is_self_sender(sender, agent_role):
        logger.info(
            "SKIP inbound: same_sender agent=%s sender=%s msg_id=%s",
            agent_role,
            sender,
            msg.id,
        )
        return True, "same_sender"

    if case_id and is_terminal(case_id) and agent_role != "coordinator":
        logger.info(
            "SKIP inbound: stale_case_id agent=%s case_id=%s msg_id=%s",
            agent_role,
            case_id,
            msg.id,
        )
        return True, "stale_case_id"

    if agent_role == "intake":
        if not is_coordinator_sender(sender):
            logger.info(
                "SKIP inbound: wrong_recipient agent=intake sender=%s msg_id=%s",
                sender,
                msg.id,
            )
            return True, "wrong_recipient"
        if case_id and stage_completed(case_id, "INTAKE_COMPLETE"):
            logger.info(
                "SKIP inbound: duplicate_stage agent=intake stage=INTAKE_COMPLETE case_id=%s",
                case_id,
            )
            return True, "duplicate_stage"

    elif agent_role == "verification":
        if not is_coordinator_sender(sender):
            logger.info(
                "SKIP inbound: wrong_recipient agent=verification sender=%s msg_id=%s",
                sender,
                msg.id,
            )
            return True, "wrong_recipient"
        if is_agent_sender(sender, "resource"):
            logger.info(
                "SKIP inbound: invalid_routing agent=verification sender=resource msg_id=%s",
                msg.id,
            )
            return True, "invalid_routing"
        if case_id and any(stage_completed(case_id, s) for s in ("CASE_CLEAR", "CASE_CAUTION", "CASE_ESCALATE")):
            logger.info(
                "SKIP inbound: already_processed agent=verification case_id=%s",
                case_id,
            )
            return True, "already_processed"

    elif agent_role == "resource":
        if not is_coordinator_sender(sender):
            logger.info(
                "SKIP inbound: wrong_recipient agent=resource sender=%s msg_id=%s",
                sender,
                msg.id,
            )
            return True, "wrong_recipient"
        if is_agent_sender(sender, "verification"):
            logger.info(
                "SKIP inbound: invalid_routing agent=resource sender=verification msg_id=%s",
                msg.id,
            )
            return True, "invalid_routing"
        if case_id and stage_completed(case_id, "RESOURCE_COMPLETE"):
            logger.info(
                "SKIP inbound: duplicate_stage agent=resource stage=RESOURCE_COMPLETE case_id=%s",
                case_id,
            )
            return True, "duplicate_stage"

    elif agent_role == "coordinator":
        payload = try_parse_json_payload(msg.content or "")
        incoming_stage = detect_stage(msg.content or "", payload)
        if (
            case_id
            and incoming_stage
            and incoming_stage in AGENT_REPLY_STAGES
            and stage_completed(case_id, incoming_stage)
            and not is_self_sender(sender, agent_role)
        ):
            logger.info(
                "SKIP inbound: duplicate_stage agent=coordinator incoming=%s case_id=%s",
                incoming_stage,
                case_id,
            )
            return True, "duplicate_stage"
        if case_id and stage_completed(case_id, "CASE_READY"):
            content_upper = (msg.content or "").upper()
            if not any(token in content_upper for token in ("NEW_CASE", "APPROVE", "REJECT", "MORE INFO")):
                logger.info(
                    "SKIP inbound: already_processed agent=coordinator case_id=%s",
                    case_id,
                )
                return True, "already_processed"

    return False, ""


def evaluate_outbound(
    agent_role: str,
    content: str,
    *,
    room_id: str,
    recipient: str = "room",
    case_id_hint: str | None = None,
) -> OutboundDecision:
    content = strip_em_dash(content or "")
    payload = try_parse_json_payload(content)
    stage = detect_stage(content, payload)
    case_id = extract_case_id(content) or (payload or {}).get("case_id") or case_id_hint
    if isinstance(case_id, str):
        case_id = case_id.upper()

    if stage == "HUMAN_ALERT" and case_id:
        ver_status = (get_verification_status(case_id) or "").upper()
        if ver_status in {"CASE_CLEAR", "CASE_CAUTION"}:
            logger.info(
                "SKIP outbound: false HUMAN_ALERT blocked case_id=%s verification=%s",
                case_id,
                ver_status,
            )
            return OutboundDecision(skip=True, reason="false_human_alert", case_id=case_id)

    if agent_role != "coordinator" and stage in {
        "VERIFY_REQUEST",
        "RESOURCE_REQUEST",
        "CASE_OPENED",
        "CASE_READY",
        "HUMAN_ALERT",
    }:
        logger.info(
            "SKIP outbound: invalid_routing agent=%s stage=%s case_id=%s",
            agent_role,
            stage,
            case_id,
        )
        return OutboundDecision(skip=True, reason="invalid_routing", stage=stage, case_id=case_id)

    if agent_role == "resource" and stage and "VERIFY" in stage:
        return OutboundDecision(skip=True, reason="invalid_routing", stage=stage, case_id=case_id)

    if stage and case_id and stage in TRACKED_STAGES:
        from core.case_state import try_claim_outbound

        if not try_claim_outbound(
            case_id,
            stage,
            agent_role,
            recipient,
            room_id=room_id,
            payload=payload,
        ):
            logger.info(
                "SKIP outbound: duplicate_stage agent=%s stage=%s case_id=%s sender=%s recipient=%s room=%s",
                agent_role,
                stage,
                case_id,
                agent_role,
                recipient,
                room_id,
            )
            return OutboundDecision(
                skip=True,
                reason="duplicate_stage",
                stage=stage,
                case_id=case_id,
            )
        record_stage(case_id, stage, payload=payload, room_id=room_id)

    if payload and stage and stage not in ROUTING_ONLY_STAGES:
        formatted = format_stage_message(stage, payload, case_id or "")
        return OutboundDecision(
            formatted_content=formatted,
            stage=stage,
            case_id=case_id,
        )

    if is_visible_json(content) and stage not in ROUTING_ONLY_STAGES:
        if payload and stage:
            formatted = format_stage_message(stage, payload, case_id or "")
            return OutboundDecision(formatted_content=formatted, stage=stage, case_id=case_id)
        logger.info(
            "SKIP outbound: raw_json_blocked agent=%s room=%s",
            agent_role,
            room_id,
        )
        return OutboundDecision(skip=True, reason="raw_json_blocked", case_id=case_id)

    return OutboundDecision(
        formatted_content=content if content else None,
        stage=stage,
        case_id=case_id,
        record_on_success=False,
    )


def extract_recipient(tool_input: dict[str, Any]) -> str:
    mentions = tool_input.get("mentions")
    if isinstance(mentions, list) and mentions:
        first = mentions[0]
        if isinstance(first, dict):
            for key in ("handle", "name", "id"):
                val = first.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip().lower()
        if isinstance(first, str):
            handle = first.lower()
            if "/" in handle:
                return handle.split("/")[-1]
            return handle.lstrip("@")
    content = tool_input.get("content", "")
    upper = content.upper()
    for handle in (
        "@MEDLABBYTBR/INTAKE",
        "@MEDLABBYTBR/VERIFICATION",
        "@MEDLABBYTBR/RESOURCE",
        "@MEDLABBYTBR/COORDINATOR",
    ):
        if handle in upper:
            return handle.split("/")[-1].lower()
    return "room"


def record_outbound_success(decision: OutboundDecision, payload: dict[str, Any] | None, room_id: str) -> None:
    """Legacy hook; stage recording now happens at claim time in evaluate_outbound."""
    return
