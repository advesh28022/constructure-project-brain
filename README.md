# Constructure Project Brain

Mini “Project Brain” for a single construction project. It ingests project PDFs, lets users chat with an AI assistant about the project, generates a door schedule, and includes a small evaluation script. Matches the Applied LLM Engineer technical assignment.

## Tech Stack

- Backend: FastAPI (Python) with Ollama LLM
- Frontend: Next.js (TypeScript)
- Retrieval: simple page-level keyword search over PDFs
- Structured extraction: door schedule JSON → table

## Backend (FastAPI)

