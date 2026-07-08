"""
Dynamically evaluates a loan applicant against whatever business rules are
currently configured (business_rules.json), without hardcoding eligibility
conditions in code.

How it stays "not hardcoded":
- Rule *values* (minimum_age, credit_score, etc.) always come fresh from the
  JSON file at evaluation time — never from a constant in code.
- The mapping below only says WHICH applicant field corresponds to WHICH rule
  field, and what kind of comparison applies (minimum / maximum / limit).
  If the manager changes a threshold via chat, this evaluator picks it up
  immediately on the next request with zero code changes.
- To support a brand-new rule field, add one line to FIELD_RULES — the
  comparison logic (>=, <=) is generic and reused.
"""

from rules_store import load_rules

DEFAULT_CATEGORY = "personal_loan"  # applicant form doesn't collect loan type yet

# Maps: rule_field_name -> (applicant_field_name, comparison_type, human_label)
# comparison_type: "min" means applicant value must be >= rule value
#                  "max" means applicant value must be <= rule value
FIELD_RULES = {
    "minimum_age":    ("age", "min", "age"),
    "maximum_age":    ("age", "max", "age"),
    "minimum_salary": ("monthlySalary", "min", "monthly salary"),
    "credit_score":   ("creditScore", "min", "credit score"),
    "loan_limit":     ("loanAmount", "max", "loan amount"),
}


def evaluate_applicant(applicant: dict, category: str = DEFAULT_CATEGORY) -> dict:
    """
    Returns {"status": "Eligible" | "Rejected", "reasons": [...]}
    Always reads the latest rules from disk — never cached, never hardcoded.
    """
    rules = load_rules().get("loan_rules", {})
    category_rules = rules.get(category, {})

    reasons = []

    for rule_field, (applicant_field, comparison, label) in FIELD_RULES.items():
        if rule_field not in category_rules:
            continue  # this rule isn't configured for this category — skip it

        required_value = category_rules[rule_field]
        applicant_value = applicant.get(applicant_field)

        if applicant_value is None:
            continue  # applicant didn't provide this field — can't evaluate it

        if comparison == "min" and applicant_value < required_value:
            reasons.append(_build_min_reason(label, required_value))

        elif comparison == "max" and applicant_value > required_value:
            reasons.append(_build_max_reason(label, required_value))

    status = "Eligible" if not reasons else "Rejected"
    return {"status": status, "reasons": reasons}


def _build_min_reason(label: str, required_value) -> str:
    display = f"₹{required_value:,}" if label in ("monthly salary",) else str(required_value)
    return f"Minimum {label} should be at least {display}."


def _build_max_reason(label: str, required_value) -> str:
    display = f"₹{required_value:,}" if label in ("loan amount",) else str(required_value)
    return f"Maximum {label} should not exceed {display}."
