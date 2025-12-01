import os
import json
from typing import List, Tuple, Dict, Any

import requests
from pypdf import PdfReader

# ------------------------------
# Simple in-memory index
# ------------------------------

IndexItem = Dict[str, Any]

INDEX_PATH = "data/index.json"
DATA_DIR = "data"


def build_index() -> None:
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    items: List[IndexItem] = []

    for fname in os.listdir(DATA_DIR):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(DATA_DIR, fname)
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            items.append(
                {
                    "file_name": fname,
                    "page": i + 1,
                    "text": text,
                }
            )

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def load_index() -> List[IndexItem]:
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------
# Retrieval
# ------------------------------

def retrieve(query: str, k: int = 5) -> List[IndexItem]:
    """Very simple keyword-based retrieval over page texts."""
    index = load_index()
    q_tokens = set(query.lower().split())

    def score(item: IndexItem) -> int:
        text_tokens = set(item["text"].lower().split())
        return len(q_tokens & text_tokens)

    scored = sorted(index, key=score, reverse=True)
    return [it for it in scored[:k] if score(it) > 0]


def build_context(chunks: List[IndexItem]) -> str:
    parts = []
    for c in chunks:
        parts.append(
            f"File: {c['file_name']} | Page: {c['page']}\n{c['text']}\n---"
        )
    return "\n\n".join(parts)


# ------------------------------
# LLM via Groq only
# ------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def call_llm(prompt: str) -> str:
    """Call Groq's OpenAI-compatible chat API."""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful construction project assistant. "
                        "Always answer using only the provided context. "
                        "If the answer is not in the context, say you don't know."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ------------------------------
# Q&A RAG
# ------------------------------

def answer_with_rag(question: str) -> Tuple[str, List[Dict[str, Any]]]:
    chunks = retrieve(question, k=5)
    context = build_context(chunks)

    prompt = f"""
You are answering questions about a construction project based only on the context below.

Context:
{context}

Question: {question}

Answer concisely in 3-5 sentences. If the answer is not clearly supported by the context, say you are not sure.
"""

    llm_output = call_llm(prompt)

    sources = [
        {"file_name": c["file_name"], "page": c["page"]}
        for c in chunks
    ]
    return llm_output.strip(), sources


# ------------------------------
# Structured door schedule
# ------------------------------

def generate_door_schedule() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    query = "doors door schedule opening schedule fire rating leaf frame"
    chunks = retrieve(query, k=8)
    context = build_context(chunks)

    schema_hint = """
Return a JSON array. Each item must be an object with keys:
- "mark" (string)
- "location" (string)
- "width_mm" (number or null)
- "height_mm" (number or null)
- "fire_rating" (string or null)
- "material" (string or null)
"""

    prompt = f"""
You are extracting a door schedule from construction documents.

Context:
{context}

Task:
Identify every door mentioned in the context and output a structured door schedule.

{schema_hint}

Rules:
- Use millimeters for width_mm and height_mm when possible; otherwise use null.
- location should be a human-readable location like "Level 1 Corridor".
- If something is not specified, set the field to null.

Respond with ONLY valid JSON, no commentary.
"""

    llm_output = call_llm(prompt)

    data: List[Dict[str, Any]] = []
    try:
        data = json.loads(llm_output)
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []

    sources = [
        {"file_name": c["file_name"], "page": c["page"]}
        for c in chunks
    ]
    return data, sources
