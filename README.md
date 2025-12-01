# Constructure Project Brain

A mini “Project Brain” for a single construction project. It ingests project PDFs, exposes a chat interface for natural‑language questions, and supports structured extraction of a door schedule using an LLM‑powered RAG pipeline. Built for the Constructure AI Applied LLM Engineer technical assignment.

---

## Live URL

Frontend (Vercel): https://constructure-project-brain.vercel.app/
Backend (Render): https://constructure-project-brain.onrender.com 

You can open the Vercel URL, chat with the assistant, and run queries against the sample project documents.

---

## How to run the FastAPI backend locally

### 1. Prerequisites

- Python 3.10+
- Groq API key (`GROQ_API_KEY`)
- Project PDFs placed in `backend/data/`

### 2. Setup

cd backend
python -m venv .venv
.venv\Scripts\activate # Windows
pip install -r requirements.txt

Set environment variables (example for Windows PowerShell):

$env:GROQ_API_KEY="gsk_your_key_here"

### 3. Start the API

uvicorn main:app --reload

- API base URL: `http://localhost:8000`
- Health check: `GET /health`
- Evaluation: `GET /eval`

On startup, the backend builds/loads a JSON index from the PDFs in `data/`.

---

## How to run the Next.js frontend locally

### 1. Prerequisites

- Node.js 18+
- npm or yarn

### 2. Setup

cd frontend
npm install

Create `.env.local`:

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

### 3. Start the dev server

npm run dev

- Frontend: `http://localhost:3000`

In production, the same `NEXT_PUBLIC_API_BASE_URL` is pointed to the Render backend URL.

---

## Required environment variables

### Backend (FastAPI)

- `GROQ_API_KEY` – GroqCloud API key for calling Llama 3.3 models.

### Frontend (Next.js)

- `NEXT_PUBLIC_API_BASE_URL` – Base URL of the FastAPI backend  
  - Local: `http://localhost:8000`  
  - Deployed: `https://<your-render-service>.onrender.com`

---

## Design notes

### Document chunking and indexing

- All provided PDFs for the sample project are placed under `backend/data/`.
- On startup, `build_index()` in `rag.py`:
  - Iterates over each PDF.
  - Splits into page‑level chunks.
  - Stores a JSON index at `backend/data/index.json` with:
    - `file_name`
    - `page`
    - `text`
- Retrieval uses simple keyword overlap scoring between the query and each page’s text, returning the top‑k pages as context.

### RAG pipeline

- `/chat` endpoint drives both free‑form Q&A and the door schedule extraction.
- For normal questions:
  - Retrieve top‑k pages from the index.
  - Build a context block: `File: <file_name> | Page: <page>` followed by page text.
  - Call Groq’s OpenAI‑compatible `/chat/completions` endpoint with a system prompt that:
    - Restricts the model to the provided context.
    - Asks it to admit when information is not present.
  - Return:
    - `type: "qa"`
    - `answer: string`
    - `sources: [{ file_name, page }]`
- The frontend displays the full conversation and renders the sources under each answer.

### Structured extraction choice

- Chosen structured task: **Door schedule extraction**.
- When the user asks for a door schedule (e.g. “Generate a door schedule”):
  - Backend retrieves pages likely to mention doors.
  - Prompts the LLM to return **only JSON** with a fixed schema:

    ```
    [
      {
        "mark": "D-101",
        "location": "Level 1 Corridor",
        "width_mm": 900,
        "height_mm": 2100,
        "fire_rating": "1 HR",
        "material": "Hollow Metal"
      }
    ]
    ```

  - Response from backend:

    ```
    {
      "type": "structured",
      "data": [ ...door objects... ],
      "sources": [{ "file_name": "...", "page": 1 }]
    }
    ```

- The frontend detects `type: "structured"` and renders a table with the schedule while still showing the list of source pages.

### Evaluation / introspection

- Endpoint: `GET /eval`.
- Contains a small set of hard‑coded queries (Q&A + door schedule).
- For each query:
  - Runs it through the same RAG / extraction pipeline.
  - Applies simple heuristics to label:
    - `looks_correct`
    - `partially_correct`
    - `wrong`
- Returns JSON:

{
"summary": {
"looks_correct": 3,
"partially_correct": 1,
"wrong": 1
},
"results": [
{
"question": "...",
"label": "looks_correct",
"sources": [ ... ]
}
]
}

Please note:

Complex tables and scanned drawings are only partially readable with lightweight text extraction.

Retrieval is keyword‑based and page‑level only, so highly specific questions (carpenter rate, exact sheet number) might require more advanced parsing or vision models
