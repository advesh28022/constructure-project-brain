import json
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

TEST_QUERIES: List[Dict[str, Any]] = [
    {"question": "What is the fire rating for corridor partitions?", "expected_hint": "fire"},
    {"question": "What is the specified flooring material in the lobby?", "expected_hint": "floor"},
    {"question": "Are there any accessibility requirements for doors?", "expected_hint": "door"},
    {"question": "Generate a door schedule", "expected_hint": "mark"},
    {"question": "What glazing is used in exterior windows?", "expected_hint": "window"},
]


@app.get("/eval")
def eval_endpoint() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []

    for item in TEST_QUERIES:
        q = item["question"]
        expected = item["expected_hint"]

        if "door schedule" in q.lower():
            data, sources = generate_door_schedule()
            text_for_check = json.dumps(data)
        else:
            answer, sources = answer_with_rag(q)
            text_for_check = answer

        label = "wrong"
        if expected.lower() in text_for_check.lower():
            label = "looks correct"
        elif any(expected.lower() in json.dumps(s).lower() for s in sources):
            label = "partially correct"

        results.append(
            {
                "question": q,
                "label": label,
                "sources": sources,
            }
        )

    summary = {
        "looks_correct": sum(r["label"] == "looks correct" for r in results),
        "partially_correct": sum(r["label"] == "partially correct" for r in results),
        "wrong": sum(r["label"] == "wrong" for r in results),
    }

    return {"summary": summary, "results": results}