from .state import AgentState
from .llm import call_llm_json
from rules_store import load_rules, save_rules
from audit_store import append_audit_entry


NO_INTENT_MESSAGE = """I couldn't identify a business rule request.

You can ask me to:
• Increase Personal Loan minimum salary to 40000
• Set Gold Loan loan limit to 700000
• Show Personal Loan rules"""

CURRENCY_FIELDS = {"minimum_salary", "loan_limit"}


def _format_value(field: str, value) -> str:
    if field in CURRENCY_FIELDS and isinstance(value, (int, float)):
        return f"₹{value:,.0f}" if value == int(value) else f"₹{value:,}"
    return str(value)


def _label(name: str) -> str:
    return name.replace("_", " ").title()


# ---------- 1. Rule Extraction Node ----------
EXTRACTION_PROMPT = """You are an assistant that extracts structured intent from a business
manager's message. The message may or may not be about business rules (loan categories).

Return ONLY a JSON object with these keys:
- category: the loan/product category, snake_case (e.g. "personal_loan", "gold_loan"). null if not mentioned or not applicable.
- field: the rule field being changed or asked about, snake_case (e.g. "minimum_salary", "minimum_age", "credit_score", "loan_limit"). null if the whole category is being asked about or not applicable.
- old_value: number if mentioned by the user, otherwise null
- new_value: the number mentioned in the message. null for "show" actions or if not applicable.
- is_relative: true if the number is a DELTA to apply on top of the current value
  (phrases like "by 10000", "by 5 years"), false if the number is the FINAL target value
  (phrases like "to 40000", "set to 21"). Always false for action "set" or "show".
- action: one of "increase", "decrease", "set", "show", "none"
  - use "show" when the manager is asking to view/see/list/check current rules.
  - use "none" if the message is small talk, a greeting, or unrelated to business rules (e.g. "Hello", "What's the weather?").

Example input: "Increase personal loan minimum salary to 40000"
Example output: {"category": "personal_loan", "field": "minimum_salary", "old_value": null, "new_value": 40000, "is_relative": false, "action": "increase"}

Example input: "Increase the minimum salary of personal loan by 10000"
Example output: {"category": "personal_loan", "field": "minimum_salary", "old_value": null, "new_value": 10000, "is_relative": true, "action": "increase"}

Example input: "Decrease gold loan minimum age by 2"
Example output: {"category": "gold_loan", "field": "minimum_age", "old_value": null, "new_value": 2, "is_relative": true, "action": "decrease"}

Example input: "Show personal loan rules"
Example output: {"category": "personal_loan", "field": null, "old_value": null, "new_value": null, "is_relative": false, "action": "show"}

Example input: "Hello"
Example output: {"category": null, "field": null, "old_value": null, "new_value": null, "is_relative": false, "action": "none"}

Example input: "What's the weather today?"
Example output: {"category": null, "field": null, "old_value": null, "new_value": null, "is_relative": false, "action": "none"}
"""


def extraction_node(state: AgentState) -> AgentState:
    result = call_llm_json(EXTRACTION_PROMPT, state["user_input"])
    state["category"] = result.get("category")
    state["field"] = result.get("field")
    state["old_value"] = result.get("old_value")
    state["new_value"] = result.get("new_value")
    state["is_relative"] = result.get("is_relative", False)
    state["action"] = result.get("action")
    return state


# ---------- 2. Validation Node ----------
def validation_node(state: AgentState) -> AgentState:
    rules = load_rules().get("loan_rules", {})

    category = state.get("category")
    field = state.get("field")
    new_value = state.get("new_value")

    # Check 1: category must be present and exist in rules
    if not category or category not in rules:
        available = ", ".join(rules.keys())
        state["is_valid"] = False
        state["validation_message"] = (
            f'Loan category "{category}" does not exist.\n'
            f"Available categories: {available}"
        )
        return state

    category_rules = rules[category]

    # Resolve relative changes ("increase by 10000") into an absolute target
    # value, using the CURRENT value from the JSON — never a stale/guessed one.
    if state.get("is_relative") and field in category_rules and new_value is not None:
        current_value = category_rules[field]
        if state.get("action") == "increase":
            new_value = current_value + new_value
        elif state.get("action") == "decrease":
            new_value = current_value - new_value
        state["new_value"] = new_value  # overwrite with the resolved absolute value

    # Check 2: field must be present and exist under that category
    if not field or field not in category_rules:
        available = ", ".join(category_rules.keys())
        state["is_valid"] = False
        state["validation_message"] = (
            f'Field "{field}" does not exist under "{category}".\n'
            f"Available fields: {available}"
        )
        return state

    # Check 3: new_value must be present at all
    if new_value is None:
        state["is_valid"] = False
        state["validation_message"] = "No new value was provided for this update."
        return state

    # Check 4: new_value must be a number (check type BEFORE comparing/using it)
    if not isinstance(new_value, (int, float)) or isinstance(new_value, bool):
        state["is_valid"] = False
        state["validation_message"] = f'The value "{new_value}" is not a valid number.'
        return state

    # Check 5: new_value must not be negative
    if new_value < 0:
        state["is_valid"] = False
        state["validation_message"] = "The requested value cannot be negative."
        return state

    current_value = category_rules[field]

    # Check 6: no-op update — old value already equals new value
    if current_value == new_value:
        state["is_valid"] = False
        state["old_value"] = current_value
        state["validation_message"] = "NO_CHANGE"
        return state

    # Check 7: cross-field logical consistency (age example)
    if field == "minimum_age" and "maximum_age" in category_rules:
        if new_value >= category_rules["maximum_age"]:
            state["is_valid"] = False
            state["validation_message"] = (
                f"Minimum age ({new_value}) cannot be greater than or equal to "
                f"the maximum age ({category_rules['maximum_age']})."
            )
            return state

    if field == "maximum_age" and "minimum_age" in category_rules:
        if new_value <= category_rules["minimum_age"]:
            state["is_valid"] = False
            state["validation_message"] = (
                f"Maximum age ({new_value}) cannot be less than or equal to "
                f"the minimum age ({category_rules['minimum_age']})."
            )
            return state

    # All checks passed
    state["old_value"] = current_value
    state["is_valid"] = True
    state["validation_message"] = "Validation passed."
    return state


# ---------- 3. Rule Update Node ----------
def update_node(state: AgentState) -> AgentState:
    if not state.get("is_valid"):
        state["updated"] = False
        return state

    data = load_rules()
    category = state["category"]
    field = state["field"]

    data["loan_rules"][category][field] = state["new_value"]
    save_rules(data)

    append_audit_entry(
        action="UPDATE",
        category=category,
        field=field,
        old_value=state["old_value"],
        new_value=state["new_value"],
    )

    state["updated"] = True
    return state


# ---------- 3b. Show Rules Node (read-only path) ----------
def show_node(state: AgentState) -> AgentState:
    rules = load_rules().get("loan_rules", {})
    category = state.get("category")

    if not category:
        if not rules:
            state["final_response"] = "No business rules are currently configured."
            return state
        lines = [_format_category(name, fields) for name, fields in rules.items()]
        state["final_response"] = "\n\n".join(lines)
        return state

    if category not in rules:
        available = ", ".join(rules.keys())
        state["final_response"] = (
            f'❌ Loan category "{category}" does not exist.\n'
            f"Available categories: {available}"
        )
        return state

    state["final_response"] = _format_category(category, rules[category])
    return state


def _format_category(category: str, fields: dict) -> str:
    title = _label(category)
    lines = [title]
    for field_name, value in fields.items():
        lines.append(f"{_label(field_name)} : {_format_value(field_name, value)}")
    return "\n".join(lines)


# ---------- 3c. No-Intent Node (small talk / unrelated messages) ----------
def no_intent_node(state: AgentState) -> AgentState:
    state["final_response"] = NO_INTENT_MESSAGE
    return state


# ---------- 4. Response Node ----------
def response_node(state: AgentState) -> AgentState:
    # Case 1: validation failed because it's a genuine no-op (old == new)
    if state.get("validation_message") == "NO_CHANGE":
        label = _label(state["field"])
        value = _format_value(state["field"], state["old_value"])
        state["final_response"] = (
            f"No changes were made.\n\nThe {label.lower()} is already {value}."
        )
        return state

    # Case 2: any other validation failure
    if not state.get("is_valid"):
        state["final_response"] = f"❌ Could not update rule: {state.get('validation_message')}"
        return state

    # Case 3: success — structured, enterprise-style confirmation
    category_label = _label(state["category"])
    field_label = _label(state["field"])
    old_display = _format_value(state["field"], state["old_value"])
    new_display = _format_value(state["field"], state["new_value"])

    state["final_response"] = (
        "Business Rule Updated\n\n"
        f"Category\n{category_label}\n\n"
        f"Field\n{field_label}\n\n"
        f"Old Value\n{old_display}\n\n"
        f"New Value\n{new_display}"
    )
    return state
