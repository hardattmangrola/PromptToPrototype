# Healthcare RAG Backend

A **secure, responsible, and modular** backend for a RAG-based Healthcare Information Assistant. It avoids hallucinations, unsupported claims, and medical advice by operating **only on provided medical documents** with strict guardrails.

## Technology Stack

| Layer | Choice |
|-------|--------|
| Language | Python |
| Framework | FastAPI |
| Auth DB | MongoDB Atlas |
| Vector DB | Pinecone (hybrid: sparse + dense) |
| Embeddings | Pinecone Inference: `llama-text-embed-v2` (dense), `pinecone-sparse-english-v0` (sparse) |
| LLM | Groq + Gemini (parallel, merged after validation) |
| Auth | JWT, RBAC (Patient / Doctor), bcrypt |

## Core Principles

- **Context-only generation** — LLM uses only retrieved chunks.
- **No answer without evidence** — Missing information → refuse.
- **Every claim traceable** — Mandatory citations.
- **Safety over helpfulness** — Refusal over hallucination.

## Project Layout

```
backend/
├── app/
│   ├── main.py              # FastAPI app, lifespan, exception handlers
│   ├── config.py            # Settings (pydantic-settings)
│   ├── api/
│   │   ├── deps.py          # Auth dependency (JWT Bearer)
│   │   └── routes/
│   │       ├── auth.py      # Login, refresh, me, register
│   │       ├── health.py    # /health, /ready
│   │       └── rag.py       # POST /rag/query
│   ├── core/
│   │   ├── security.py      # JWT, bcrypt
│   │   ├── rbac.py          # require_roles(Patient|Doctor)
│   │   └── exceptions.py    # AppException, RefusalError
│   ├── db/
│   │   ├── mongodb.py       # Motor client, get_db, collections
│   │   └── models.py        # UserInDB, RefusalLogEntry
│   ├── schemas/             # Pydantic request/response
│   └── services/
│       ├── auth_service.py
│       ├── intent_classifier.py   # Allowed vs forbidden question categories
│       ├── embeddings.py          # Dense + sparse via Pinecone Inference
│       ├── retrieval.py           # Hybrid query, threshold, dedupe
│       ├── llm/                   # Groq, Gemini, orchestrator, prompts
│       ├── validation.py          # Claim-context, citations, safety, merge
│       └── rag_pipeline.py        # Full pipeline + refusal logging
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. **Python 3.10+**, create a venv and install:

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **Environment**: Copy `.env.example` to `.env` and set:

   - `MONGODB_URI` — MongoDB Atlas connection string
   - `JWT_SECRET_KEY` — Long random secret for JWT
   - `PINECONE_API_KEY` — Pinecone API key
   - `GROQ_API_KEY`, `GEMINI_API_KEY` — LLM API keys

3. **Pinecone**: Create a hybrid index (dense + sparse) and ingest your medical document chunks with:

   - Dense vectors: Pinecone Inference `llama-text-embed-v2`
   - Sparse vectors: Pinecone Inference `pinecone-sparse-english-v0`

   Set `PINECONE_INDEX_NAME` (or `PINECONE_HOST`) in `.env`.

4. **MongoDB**: Ensure collections `users` and `refusal_logs` exist (created on first use). Create a user (e.g. via `/api/v1/auth/register`) with `role`: `patient` or `doctor`.

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `GET /api/v1/health`, `GET /api/v1/ready`

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register (patient/doctor) |
| POST | `/api/v1/auth/login` | No | Login → access + refresh token |
| POST | `/api/v1/auth/refresh` | No | New tokens from refresh token |
| GET | `/api/v1/auth/me` | Bearer | Current user |
| GET | `/api/v1/health` | No | Liveness |
| GET | `/api/v1/ready` | No | Readiness (DB) |
| POST | `/api/v1/rag/query` | Bearer | RAG question → answer + citations or refusal |

**RAG request body:** `{"query": "...", "top_k": 10, "include_metadata": true}`  
**Response:** Either `RAGResponse` (answer, citations, limitations) or `RefusalResponse` (refused, message, reason).

## Question Classification & Refusal

- **Allowed**: Factual lookup, definitions, guideline navigation, doc-bound comparisons, eligibility/criteria, summarization, citation/traceability.
- **Forbidden** (always refused): Diagnosis, personalized treatment, medical advice, external/best-treatment questions.

Refusals are logged in `refusal_logs` for audit when `LOG_REFUSALS=true`.

## Hallucination Prevention

- Intent classification before retrieval.
- Hybrid retrieval with similarity threshold and section-aware deduplication.
- Context-only prompts; low temperature; structured JSON with citations.
- Post-generation: claim–context consistency, citation enforcement, cross-model agreement (Groq vs Gemini), safety filter.
- Merge only validated overlapping content; conservative phrasing.

## Security & RBAC

- JWT access (short-lived) + refresh tokens.
- Roles: `patient`, `doctor`. Use `require_roles(Role.PATIENT)` or `require_doctor()` where needed.
- No medical data leakage between users (enforce in your data layer/namespace by `user_id`/role if required).

## Limitations & Disclaimer

This system does **not** provide medical advice, diagnosis, or personalized treatment. It only surfaces information from ingested documents with citations. Always advise users to consult a qualified healthcare professional.
