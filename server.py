import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from chat.bot import chat

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
# Rachel — multilingual voice, works reasonably for Hindi too
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

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


class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
        raise HTTPException(status_code=503, detail="ElevenLabs API key not configured")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": req.text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="ElevenLabs TTS failed")

    return StreamingResponse(
        iter([resp.content]),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
