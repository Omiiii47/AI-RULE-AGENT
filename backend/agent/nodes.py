from .state import AgentState
from .llm import call_llm_json, call_llm_text
from rules_store import load_rules, save_rules


# ---------- 1. Rule Extraction Node ----------
EXTRACTION_PROMPT = """You are an assistant that extracts structured intent from a business
manager's instruction to modify a business rule.

Return ONLY a JSON object with these keys:
- category: the loan/product category, snake_case (e.g. "personal_loan", "gold_loan")
- field: the rule field being changed, snake_case (e.g. "minimum_salary", "minimum_age", "credit_score", "loan_limit")
- old_value: number if mentioned by the user, otherwise null
- new_value: number, the target value being requested
- action: one of "increase", "decrease", "set"

Example input: "Increase personal loan minimum salary to 40000"
Example output: {"category": "personal_loan", "field": "minimum_salary", "old_value": null, "new_value": 40000, "action": "increase"}
"""


def extraction_node(state: AgentState) -> AgentState:
    result = call_llm_json(EXTRACTION_PROMPT, state["user_input"])
    state["category"] = result.get("category")
    state["field"] = result.get("field")
    state["old_value"] = result.get("old_value")
    state["new_value"] = result.get("new_value")
    state["action"] = result.get("action")
    return state


# ---------- 2. Validation Node ----------
def validation_node(state: AgentState) -> AgentState:
    rules = load_rules().get("loan_rules", {})

    category = state.get("category")
    field = state.get("field")
    new_value = state.get("new_value")

    # Rule 1: category must exist
    if category not in rules:
        state["is_valid"] = False
        state["validation_message"] = f"No business rule category found for '{category}'."
        return state

    # Rule 2: field must exist under that category
    if field not in rules[category]:
        state["is_valid"] = False
        state["validation_message"] = (
            f"Field '{field}' does not exist under '{category}'."
        )
        return state

    # Rule 3: new_value must be a valid number
    if new_value is None or not isinstance(new_value, (int, float)):
        state["is_valid"] = False
        state["validation_message"] = "The requested new value is missing or invalid."
        return state

    # Rule 4: sanity check — no negative values
    if new_value < 0:
        state["is_valid"] = False
        state["validation_message"] = "The requested value cannot be negative."
        return state

    # Capture the true current value (overrides any guess from extraction)
    state["old_value"] = rules[category][field]
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

    state["updated"] = True
    return state


# ---------- 4. Response Node ----------
RESPONSE_PROMPT = """You are a helpful assistant replying to a business manager who just
requested a business rule change. Write ONE short, clear sentence confirming the outcome.
Use ₹ for currency-like fields (salary, loan_limit). Do not add extra explanation."""


def response_node(state: AgentState) -> AgentState:
    if not state.get("is_valid"):
        state["final_response"] = f"❌ Could not update rule: {state.get('validation_message')}"
        return state

    context = (
        f"Category: {state['category']}, Field: {state['field']}, "
        f"Old value: {state['old_value']}, New value: {state['new_value']}"
    )
    state["final_response"] = call_llm_text(RESPONSE_PROMPT, context)
    return state
