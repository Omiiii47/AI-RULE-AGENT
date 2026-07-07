from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph import agent_app

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
