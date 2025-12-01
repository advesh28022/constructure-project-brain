from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple

from rag import answer_with_rag, generate_door_schedule, build_index, load_index

app = FastAPI()

# CORS – relaxed so Vercel + localhost both work
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build index on startup if needed
@app.on_event("startup")
def startup_event():
    try:
        load_index()
    except Exception:
        build_index()


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    msg = req.message.lower()

    # Simple mode detection: door schedule trigger
    if "door schedule" in msg or ("door" in msg and "schedule" in msg):
        data, sources = generate_door_schedule()
        return {
            "type": "structured",
            "data": data,
            "sources": sources,
        }

    # Default RAG Q&A
    answer, sources = answer_with_rag(req.message)
    return {
        "type": "qa",
        "answer": answer,
        "sources": sources,
    }


# ----- Minimal evaluation endpoint -----

TEST_QUERIES: List[Tuple[str, str]] = [
    ("What is the fire rating for corridor partitions?", "fire rating"),
    ("What is the specified flooring material in the lobby?", "floor"),
    ("Are there any accessibility requirements for doors?", "door"),
    ("Generate a door schedule", "door schedule"),
    ("What type of glazing is used in exterior windows?", "window"),
]


@app.get("/eval")
def eval_endpoint() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []

    for q, expected_hint in TEST_QUERIES:
        ans, sources = answer_with_rag(q) if "door schedule" not in q.lower() else generate_door_schedule()
        if isinstance(ans, tuple):
            # if generate_door_schedule returned (data, sources)
            data, sources = ans
            text_for_check = str(data)
        else:
            text_for_check = ans

        label = "wrong"
        if expected_hint.lower() in text_for_check.lower():
            label = "looks correct"
        elif any(expected_hint.lower() in (s["file_name"] or "").lower() for s in sources):
            label = "partially correct"

        results.append(
            {
                "question": q,
                "label": label,
                "sources": sources,
            }
        )

    summary = {
        "looks_correct": sum(1 for r in results if r["label"] == "looks correct"),
        "partially_correct": sum(1 for r in results if r["label"] == "partially correct"),
        "wrong": sum(1 for r in results if r["label"] == "wrong"),
    }

    return {"summary": summary, "results": results}
