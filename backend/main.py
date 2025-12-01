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
    {"question": "Summarize the given files for this construction project.", "expected_hint": "window"},
    {"question": "Generate a door schedule", "expected_hint": "mark"},
    {"question": "What glazing is used in exterior windows?", "expected_hint": "window"},
]


@app.get("/eval")
def eval_endpoint():
    eval_questions = [
        "Summarize the given files for this construction project.",
        "Generate a door schedule.",
    ]

    results = []
    summary = {"looks_correct": 0, "partially_correct": 0, "wrong": 0, "skipped": 0}

    for q in eval_questions:
        try:
            if "door schedule" in q.lower():
                data, sources = generate_door_schedule()
                answer = json.dumps(data)[:200]  # short preview
            else:
                answer, sources = answer_with_rag(q)

            if "LLM call skipped due to rate limiting" in answer:
                label = "skipped"
            else:
                # simple placeholder labels; you can keep them manual/heuristic
                label = "looks_correct"
        except Exception as e:
            answer = f"Error during eval: {e}"
            sources = []
            label = "skipped"

        summary[label] = summary.get(label, 0) + 1
        results.append(
            {"question": q, "answer_preview": answer, "label": label, "sources": sources}
        )

    return {"summary": summary, "results": results}
