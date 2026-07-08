import json
from datetime import datetime
from pathlib import Path

AUDIT_FILE = Path(__file__).parent / "audit_log.json"


def load_audit_log() -> list:
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def append_audit_entry(
    action: str,
    category: str,
    field: str,
    old_value,
    new_value,
    user: str = "Manager",
) -> None:
    """Appends one entry to the audit log. Called after every successful rule change."""
    logs = load_audit_log()

    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,              # CREATE / UPDATE / DELETE
        "category": category,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
    }

    logs.append(entry)

    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
