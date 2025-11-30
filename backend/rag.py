import os
import json
from typing import List, Dict, Tuple

from pypdf import PdfReader
import requests

# ----- Simple in-memory index (no vector DB) -----

# Each entry: {"file_name": ..., "page": int, "text": str}
_INDEX: List[Dict] = []


def build_index():
    """
    Load all PDFs in ./data into a simple list of pages
    we can scan with keyword matching.
    """
    global _INDEX
    _INDEX = []

    data_dir = "data"
    if not os.path.isdir(data_dir):
        print("No data directory found")
        return _INDEX

    for fname in os.listdir(data_dir):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(data_dir, fname)
        reader = PdfReader(path)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue
            _INDEX.append(
                {
                    "file_name": fname,
                    "page": page_num + 1,
                    "text": text,
                }
            )

    print(f"Indexed {len(_INDEX)} pages from PDFs in {data_dir}")
    return _INDEX


def ensure_index():
    if not _INDEX:
        build_index()


def retrieve(query: str, k: int = 5) -> List[Tuple[str, Dict]]:
    """
    Very simple keyword retrieval:
    - Score each page by how many query words it contains.
    - Return top-k pages.
    """
    ensure_index()
    if not _INDEX:
        return []

    words = [w.lower() for w in query.split() if len(w) > 2]
    scores: List[Tuple[int, Dict]] = []

    for entry in _INDEX:
        text_lower = entry["text"].lower()
        score = sum(text_lower.count(w) for w in words)
        if score > 0:
            scores.append((score, entry))

    scores.sort(key=lambda x: x[0], reverse=True)
    top = scores[:k]

    results: List[Tuple[str, Dict]] = []
    for score, entry in top:
        snippet = entry["text"][:2000]
        meta = {"file_name": entry["file_name"], "page": entry["page"]}
        results.append((snippet, meta))

    return results


def answer_with_rag(question: str):
    """RAG-like answer using keyword retrieval + Ollama."""
    contexts = retrieve(question)
    context_text = ""
    source_meta = []
    for i, (doc, meta) in enumerate(contexts):
        context_text += f"[{i}] (file={meta['file_name']}, page={meta['page']})\n{doc}\n\n"
        source_meta.append(meta)

    if not context_text:
        prompt = f"You have no context. The user asked: {question}. Say you are not sure."
    else:
        prompt = f"""
You are a construction project assistant.
Use ONLY the context below from project documents.
If you are not sure, say you are not sure and do not invent details.

Context:
{context_text}

Question: {question}

Answer in 3-5 sentences. Explicitly mention which file and page you used.
"""

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    answer = data.get("response", "")

    return answer, source_meta


# ----- Mode routing & simple extraction stubs -----

def detect_mode(user_message: str) -> str:
    msg = user_message.lower()
    if "door schedule" in msg:
        return "door_schedule"
    return "qa"


def extract_door_schedule(question: str):
    """
    Use retrieval to get door-related pages, then ask Ollama to output
    a JSON door schedule.
    """
    # 1) Retrieve relevant context
    contexts = retrieve("door schedule door openings doors")
    context_text = ""
    sources = []
    for i, (doc, meta) in enumerate(contexts):
        context_text += f"[{i}] (file={meta['file_name']}, page={meta['page']})\n{doc}\n\n"
        sources.append(meta)

    # 2) Define schema for doors
    schema_description = """
Return a JSON array of door objects. Each object has:
- mark: string (door mark / ID)
- location: string (e.g. Level 1 Corridor)
- width_mm: number or null
- height_mm: number or null
- fire_rating: string or null
- material: string or null
"""

    # 3) Build prompt for Ollama
    prompt = f"""
You are extracting a DOOR SCHEDULE from construction documents.

The user asked: {question}

Context:
{context_text}

Task:
From the context, extract all doors you can find and return them as JSON only,
following this schema:
{schema_description}

Important:
- If a field is missing, use null.
- Ensure JSON is valid.
- Do not add any text before or after the JSON.
"""

    # 4) Call Ollama
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    raw = data.get("response", "")

    # 5) Parse JSON safely
    doors = []
    try:
        # try to locate first '[' and last ']'
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            json_str = raw[start : end + 1]
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                doors = parsed
    except Exception:
        doors = []

    return doors, sources

