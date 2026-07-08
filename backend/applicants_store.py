import json
import uuid
from datetime import datetime
from pathlib import Path

APPLICANTS_FILE = Path(__file__).parent / "applicants.json"


def load_applicants() -> list:
    with open(APPLICANTS_FILE, "r") as f:
        return json.load(f)


def save_applicant(applicant_data: dict, status: str, reasons: list) -> dict:
    """Appends one applicant record (with evaluation result) and returns the saved record."""
    applicants = load_applicants()

    record = {
        "applicationId": str(uuid.uuid4()),
        "name": applicant_data.get("name"),
        "age": applicant_data.get("age"),
        "monthlySalary": applicant_data.get("monthlySalary"),
        "creditScore": applicant_data.get("creditScore"),
        "employmentType": applicant_data.get("employmentType"),
        "loanAmount": applicant_data.get("loanAmount"),
        "status": status,
        "reasons": reasons,
        "submittedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    applicants.append(record)

    with open(APPLICANTS_FILE, "w") as f:
        json.dump(applicants, f, indent=2, ensure_ascii=False)

    return record
