from typing import List, Literal, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import answer_with_rag, detect_mode, extract_door_schedule
from eval import evaluate


app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://constructure-project-brain.vercel.app",
    "https://constructure-project-brain-nbvy0bwwx-adveshs-projects-4796d1f6.vercel.app",
    "https://constructure-project-brain-jiminwg05-adveshs-projects-4796d1f6.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class SourceMeta(BaseModel):
    file_name: str
    page: int


class ChatResponse(BaseModel):
    type: Literal["qa", "structured"]
    answer: str | None = None
    data: Any | None = None
    sources: List[SourceMeta] = []


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/eval")
def run_eval():
    return {"results": evaluate()}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    mode = detect_mode(req.message)

    if mode == "door_schedule":
        doors, sources = extract_door_schedule(req.message)
        src_objs = [SourceMeta(file_name=s["file_name"], page=s["page"]) for s in sources]
        return ChatResponse(type="structured", data=doors, sources=src_objs)

    answer, sources = answer_with_rag(req.message)
    src_objs = [SourceMeta(file_name=s["file_name"], page=s["page"]) for s in sources]
    return ChatResponse(type="qa", answer=answer, sources=src_objs)
