"""Load sector-specific prompts and data based on per-request sector context."""
import json
import os
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_local = threading.local()

SECTORS = [
    "pharmacy",
    "hospital_triage",
    "lab",
    "mental_health",
    "hmo_claims",
    "emergency",
]

HUMAN_ROLES = {
    "pharmacy": "Pharmacist",
    "hospital_triage": "Doctor / Nurse",
    "lab": "Lab Officer",
    "mental_health": "Clinical Coordinator",
    "hmo_claims": "Claims Officer",
    "emergency": "Dispatcher",
}

SECTOR_META = {
    "pharmacy": {"label": "Pharmacy", "color": "#00c896", "icon": "💊"},
    "hospital_triage": {"label": "Hospital Triage", "color": "#4da6ff", "icon": "🏥"},
    "lab": {"label": "Lab / Diagnostics", "color": "#a78bfa", "icon": "🔬"},
    "mental_health": {"label": "Mental Health", "color": "#2dd4bf", "icon": "🧠"},
    "hmo_claims": {"label": "HMO / Insurance", "color": "#fbbf24", "icon": "📋"},
    "emergency": {"label": "Emergency Dispatch", "color": "#ef4444", "icon": "🚨"},
}

SECTOR_DISPLAY_NAMES = {
    "pharmacy": "Pharmacy",
    "hospital_triage": "Hospital Triage",
    "lab": "Lab and Diagnostics",
    "mental_health": "Mental Health",
    "hmo_claims": "HMO and Insurance Claims",
    "emergency": "Emergency Dispatch",
}

VERIFICATION_DATA_FILES = {
    "pharmacy": ["registry.json", "risk_table.json"],
    "hospital_triage": ["triage_criteria.json"],
    "lab": ["test_catalog.json", "referral_rules.json"],
    "mental_health": ["risk_screening.json"],
    "hmo_claims": ["policy_rules.json", "coverage_limits.json"],
    "emergency": ["severity_rules.json"],
}

RESOURCE_DATA_FILES = {
    "pharmacy": ["resources.json"],
    "hospital_triage": ["beds.json"],
    "lab": ["lab_slots.json"],
    "mental_health": ["therapist_availability.json"],
    "hmo_claims": ["coverage_table.json"],
    "emergency": ["units.json"],
}


def set_active_sector(sector: str) -> None:
    if sector not in SECTORS:
        raise ValueError(f"Unknown sector: {sector}. Must be one of {SECTORS}")
    _local.sector = sector


def get_active_sector() -> str:
    return getattr(_local, "sector", os.getenv("ACTIVE_SECTOR", "pharmacy"))


def set_sector(sector: str) -> None:
    """Set per-request sector; also updates env for worker subprocess compatibility."""
    set_active_sector(sector)
    os.environ["ACTIVE_SECTOR"] = sector


def sector_slug(sector: str | None = None) -> str:
    """Uppercase sector token for Band room names (e.g. pharmacy -> PHARMACY)."""
    s = sector or get_active_sector()
    return s.upper().replace("_", "")


def sector_meta(sector: str | None = None) -> dict:
    s = sector or get_active_sector()
    return SECTOR_META.get(s, {"label": s, "color": "#00c896", "icon": "🏥"})


def load_prompt(agent_name: str) -> str:
    path = ROOT / "prompts" / get_active_sector() / f"{agent_name}.md"
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_data(filename: str) -> dict | list:
    path = ROOT / "data" / get_active_sector() / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_verification_data() -> dict:
    sector = get_active_sector()
    return {
        f.replace(".json", ""): load_data(f)
        for f in VERIFICATION_DATA_FILES.get(sector, [])
    }


def load_resource_data() -> dict:
    sector = get_active_sector()
    return {
        f.replace(".json", ""): load_data(f)
        for f in RESOURCE_DATA_FILES.get(sector, [])
    }


def _normalize_query(text: str) -> str:
    return (text or "").strip().lower()


def _item_matches_query(item: dict, query: str, fields: list[str]) -> bool:
    if not query:
        return False
    for field in fields:
        value = item.get(field)
        if not isinstance(value, str):
            continue
        lowered = value.lower()
        if query in lowered or lowered in query:
            return True
    return False


def _filter_items(items: list, query: str, fields: list[str], limit: int = 3) -> list:
    if not items:
        return []
    query = _normalize_query(query)
    if not query:
        return items[:limit]

    exact = [item for item in items if _item_matches_query(item, query, fields)]
    if exact:
        return exact[:limit]

    tokens = [token for token in query.replace(",", " ").split() if len(token) > 2]
    partial = []
    for item in items:
        if any(_item_matches_query(item, token, fields) for token in tokens):
            partial.append(item)
    if partial:
        return partial[:limit]

    return items[:1]


def _filter_dict_data(data: dict | list, query: str, field_map: dict[str, list[str]], limit: int = 3) -> dict | list:
    if isinstance(data, list):
        return _filter_items(data, query, field_map.get("_root", ["name"]), limit)

    filtered: dict = {}
    for key, value in data.items():
        fields = field_map.get(key, ["name"])
        if isinstance(value, list):
            filtered[key] = _filter_items(value, query, fields, limit)
        else:
            filtered[key] = value
    return filtered


VERIFICATION_FIELD_MAP = {
    "pharmacy": {
        "registry": {"drugs": ["drug_name"]},
        "risk_table": {"interactions": ["drug_name", "interacts_with"]},
        "doctors": {"doctors": ["doctor_code", "doctor_name"]},
        "hospitals": {"hospitals": ["hospital_code", "hospital_name"]},
    },
    "hospital_triage": {
        "triage_criteria": {"rules": ["protocol"]},
    },
    "lab": {
        "test_catalog": {"tests": ["test_name"]},
        "referral_rules": {"rules": ["test_name"]},
    },
    "mental_health": {
        "risk_screening": {"criteria": ["protocol"]},
    },
    "hmo_claims": {
        "policy_rules": {"policies": ["policy_number", "holder_name"]},
        "coverage_limits": {"limits": ["policy_number"]},
    },
    "emergency": {
        "severity_rules": {"rules": ["condition", "protocol"]},
    },
}

RESOURCE_FIELD_MAP = {
    "pharmacy": {"resources": {"inventory": ["drug_name"]}},
    "hospital_triage": {"beds": {"wards": ["ward_name", "bed_type"]}},
    "lab": {"lab_slots": {"slots": ["test_name"]}},
    "mental_health": {"therapist_availability": {"therapists": ["therapist_name", "specialty"]}},
    "hmo_claims": {"coverage_table": {"coverage": ["procedure_code", "procedure_name"]}},
    "emergency": {"units": {"units": ["unit_id", "unit_type"]}},
}


def _combined_query(requested_service: str, intake_result: dict | None) -> str:
    intake_result = intake_result or {}
    parts = [
        requested_service,
        intake_result.get("requested_service"),
        intake_result.get("chief_complaint"),
        intake_result.get("presenting_issue"),
        intake_result.get("prescription_code"),
        intake_result.get("referral_number"),
        intake_result.get("procedure_code"),
        intake_result.get("emergency_type"),
    ]
    return " ".join(str(part) for part in parts if part)


def _filter_triage_rules(rules: list, query: str, intake_result: dict | None) -> list:
    text = _combined_query(query, intake_result)
    if not text:
        return rules[:2]
    matches = []
    for rule in rules:
        keywords = rule.get("symptom_keywords") or []
        if any(keyword.lower() in text.lower() for keyword in keywords):
            matches.append(rule)
    return matches[:3] if matches else rules[:2]


def load_verification_data_for(
    requested_service: str,
    intake_result: dict | None = None,
) -> dict:
    """Return only verification records relevant to the requested service."""
    sector = get_active_sector()
    query = _combined_query(requested_service, intake_result)
    full = load_verification_data()
    field_map = VERIFICATION_FIELD_MAP.get(sector, {})
    filtered: dict = {}

    for dataset_name, dataset in full.items():
        mapping = field_map.get(dataset_name, {})
        if dataset_name == "triage_criteria" and isinstance(dataset, dict):
            rules = dataset.get("rules", [])
            filtered[dataset_name] = {"rules": _filter_triage_rules(rules, query, intake_result)}
            continue

        if isinstance(dataset, dict):
            reduced = {}
            for key, items in dataset.items():
                if isinstance(items, list):
                    fields = mapping.get(key, ["name"])
                    reduced[key] = _filter_items(items, query, fields)
                else:
                    reduced[key] = items
            filtered[dataset_name] = reduced
        elif isinstance(dataset, list):
            fields = mapping.get("_root", ["name"])
            filtered[dataset_name] = _filter_items(dataset, query, fields)
        else:
            filtered[dataset_name] = dataset

    if sector == "pharmacy":
        prescription_code = (intake_result or {}).get("prescription_code")
        if prescription_code:
            try:
                doctors = load_data("doctors.json")
                filtered["doctors"] = {
                    "doctors": _filter_items(
                        doctors.get("doctors", []),
                        prescription_code,
                        ["doctor_code"],
                        limit=1,
                    )
                }
                matched = filtered["doctors"]["doctors"]
                if matched:
                    hospital_code = matched[0].get("hospital_code")
                    hospitals = load_data("hospitals.json")
                    filtered["hospitals"] = {
                        "hospitals": [
                            hospital
                            for hospital in hospitals.get("hospitals", [])
                            if hospital.get("hospital_code") == hospital_code
                        ][:1]
                    }
            except FileNotFoundError:
                pass

    return filtered


def load_resource_data_for(
    requested_service: str,
    intake_result: dict | None = None,
) -> dict:
    """Return only resource records relevant to the requested service."""
    sector = get_active_sector()
    query = _combined_query(requested_service, intake_result)
    full = load_resource_data()
    field_map = RESOURCE_FIELD_MAP.get(sector, {})
    filtered: dict = {}

    for dataset_name, dataset in full.items():
        mapping = field_map.get(dataset_name, {})
        if isinstance(dataset, dict):
            reduced = {}
            for key, items in dataset.items():
                if isinstance(items, list):
                    fields = mapping.get(key, ["name"])
                    if sector == "emergency" and key == "units":
                        emergency_type = (intake_result or {}).get("emergency_type", query).lower()
                        type_map = {
                            "fire": "fire",
                            "medical": "ambulance",
                            "cardiac": "ambulance",
                            "crime": "police",
                            "police": "police",
                        }
                        unit_type = next(
                            (mapped for token, mapped in type_map.items() if token in emergency_type),
                            None,
                        )
                        if unit_type:
                            typed = [item for item in items if item.get("unit_type") == unit_type]
                            reduced[key] = _filter_items(
                                typed or items,
                                query,
                                fields,
                                limit=2,
                            )
                        else:
                            reduced[key] = _filter_items(items, query, fields)
                    else:
                        reduced[key] = _filter_items(items, query, fields)
                else:
                    reduced[key] = items
            filtered[dataset_name] = reduced
        elif isinstance(dataset, list):
            fields = mapping.get("_root", ["name"])
            filtered[dataset_name] = _filter_items(dataset, query, fields)
        else:
            filtered[dataset_name] = dataset

    return filtered


def human_role(sector: str | None = None) -> str:
    return HUMAN_ROLES.get(sector or get_active_sector(), "Human Professional")


def _load_institutions_index() -> dict:
    path = ROOT / "data" / "institutions.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_institutions(sector: str | None = None) -> list:
    sector = sector or get_active_sector()
    return _load_institutions_index().get(sector, [])


def get_institution(sector: str, institution_id: str) -> dict | None:
    for inst in load_institutions(sector):
        if inst.get("id") == institution_id:
            return inst
    return None


def load_institution_users() -> list:
    path = ROOT / "data" / "institution_users.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("institutions", [])


def get_institution_user(sector: str, institution_id: str) -> dict | None:
    for user in load_institution_users():
        if user.get("sector") == sector and user.get("institution_id") == institution_id:
            return user
    return None


def band_room_name(
    case_id: str,
    sector: str | None = None,
    institution_id: str | None = None,
) -> str:
    sec = sector_slug(sector)
    if institution_id:
        return f"MedBand-{sec}-{institution_id}-{case_id}"
    return f"MedBand-{sec}-{case_id}"
