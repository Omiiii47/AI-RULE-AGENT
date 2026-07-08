import json
from pathlib import Path

RULES_FILE = Path(__file__).parent / "business_rules.json"


def load_rules() -> dict:
    with open(RULES_FILE, "r") as f:
        return json.load(f)


def save_rules(rules: dict) -> None:
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
