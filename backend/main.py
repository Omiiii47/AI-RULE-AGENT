from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from agent.graph import agent_app
from audit_store import load_audit_log
from applicant_rules_evaluator import evaluate_applicant
from applicants_store import save_applicant

app = FastAPI(title="Business Rule Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # MVP only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ApplicantRequest(BaseModel):
    name: str
    age: int
    monthlySalary: float
    creditScore: int
    employmentType: str
    loanAmount: float


@app.post("/chat")
def chat(req: ChatRequest):
    initial_state = {"user_input": req.message}
    result = agent_app.invoke(initial_state)
    return {"response": result["final_response"]}


@app.get("/audit-log")
def audit_log():
    """Returns the full history of rule changes, most recent first."""
    logs = load_audit_log()
    return {"logs": list(reversed(logs))}


@app.post("/apply")
def apply(req: ApplicantRequest):
    """
    Evaluates a loan applicant against the LATEST configured business rules
    (read fresh from business_rules.json on every call — never hardcoded),
    then stores the applicant record with the result regardless of outcome.
    """
    applicant_data = req.dict()

    evaluation = evaluate_applicant(applicant_data)

    record = save_applicant(
        applicant_data=applicant_data,
        status=evaluation["status"],
        reasons=evaluation["reasons"],
    )

    return {
        "applicationId": record["applicationId"],
        "status": record["status"],
        "reasons": record["reasons"],
        "submittedAt": record["submittedAt"],
    }
