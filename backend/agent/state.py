from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    user_input: str          # raw manager message

    # Extraction Node output
    category: Optional[str]      # e.g. "personal_loan"
    field: Optional[str]         # e.g. "minimum_salary"
    old_value: Optional[float]
    new_value: Optional[float]
    is_relative: Optional[bool]  # True if new_value is a delta ("by X"), not a target ("to X")
    action: Optional[str]        # e.g. "increase" / "decrease" / "set"

    # Validation Node output
    is_valid: bool
    validation_message: Optional[str]

    # Update Node output
    updated: bool

    # Response Node output
    final_response: str
