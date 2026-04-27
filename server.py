import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from chat.bot import chat

app = FastAPI(title="Shri Mataji Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

_sessions: dict = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    language: Optional[str] = "en"  # "en" or "hi"


class ChatResponse(BaseModel):
    answer: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    history = _sessions.get(req.session_id, [])
    # Prepend language hint to message so Claude detects intent
    message = req.message
    if req.language == "hi":
        message = f"[उपयोगकर्ता हिंदी में उत्तर चाहता है] {req.message}"
    try:
        answer, updated_history = chat(message, history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    _sessions[req.session_id] = updated_history
    return ChatResponse(answer=answer, session_id=req.session_id)


@app.delete("/chat/{session_id}")
def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"cleared": session_id}


@app.get("/health")
def health():
    return {"status": "ok"}
