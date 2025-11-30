# Constructure Project Brain

Mini “Project Brain” for a single construction project. It ingests project PDFs, lets users chat with an AI assistant about the project, generates a door schedule, and includes a small evaluation script.

## Tech Stack

- Backend: FastAPI (Python) with Ollama LLM
- Frontend: Next.js (TypeScript)
- Retrieval: simple page-level keyword search over PDFs
- Structured extraction: door schedule JSON → table

## Backend (FastAPI)

cd backend
python -m venv .venv

Windows: .venv\Scripts\activate
Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
python ingest.py # index PDFs from backend/data
uvicorn main:app --reload

## Frontend (Next.js)

cd frontend
npm install
npm run dev

Set environment variable:

- `NEXT_PUBLIC_API_BASE_URL` – URL of the FastAPI backend.

## Features

- Ingest PDFs into a searchable index (file name + page + text).
- RAG-style chat UI: ask natural questions, get answers with file/page citations.
- Structured extraction: type **“Generate a door schedule”** to get a door schedule table.
- Evaluation: `backend/eval.py` and `/eval` endpoint run 5+ test queries and label answers as `looks correct / partially correct / wrong`.

Deployment URLs (to be filled ):

- Frontend (Vercel): `https://...`
- Backend (Render): `https://...`
