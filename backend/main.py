from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph import agent_app
from audit_store import load_audit_log

app = FastAPI(title="Business Rule Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # MVP only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


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
