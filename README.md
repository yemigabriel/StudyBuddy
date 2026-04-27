# StudyBuddy

StudyBuddy is a full-stack AI study assistant that turns uploaded documents into:

- chat answers
- summaries
- quizzes
- flashcards

It uses a RAG pipeline, OpenAI-powered agents, S3-backed memory, and AWS deployment with Terraform.

## Architecture

```text
Frontend (Next.js static export on S3 + CloudFront)
  -> Upload-files
  -> Sends chat / summary / quiz / flashcards requests
  -> Renders chat, quiz modal, and flashcards modal

Backend (FastAPI on AWS Lambda via Mangum)
  -> Parses documents
  -> Chunks content
  -> Retrieves context from vector store
  -> Calls OpenAI for QA or OpenAI Agents SDK for summary / quiz / flashcards
  -> Persists session memory locally + S3

Storage
  -> S3 frontend bucket
  -> S3 memory bucket
  -> Chroma (local dev) or Pinecone (production)
```

## Current Features

- `POST /upload`, `POST /chat`, `POST /chat/stream`, `GET /health`
- Multi-format ingestion:
  - `pdf`, `docx`, `md`, `txt`, `csv`, `json`, `html`, `xml`, `xlsx`, `pptx`
- PDF parsing with `pymupdf4llm` and OCR fallback
- Query rewriting for follow-up questions
- Disambiguation when multiple documents exist
- Session-level remembered document selection
- Modes:
  - `qa`
  - `summary`
  - `quiz`
  - `flashcards`
- Streaming chat responses locally
- Upload-first frontend flow
- Quiz and flashcards modal UI
- Pytest backend test suite with endpoint coverage
- Terraform-based AWS deployment
- GitHub Actions CI/CD pipeline

## Retrieval Pipeline

1. rewrite query
2. retrieve context
3. rerank chunks
4. pass context to QA / agent mode

## Backend Stack

- FastAPI
- Mangum
- OpenAI Python SDK
- OpenAI Agents SDK
- ChromaDB / Pinecone
- boto3

## Frontend Stack

- Next.js
- TypeScript
- Tailwind CSS

## Local Development

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn server:app --reload
```

Run tests:

```bash
cd backend
UV_CACHE_DIR=.uv-cache uv run pytest tests -q
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## Environment

### Backend

Expected environment variables include:

- `OPENAI_API_KEY`
- `VECTOR_DB=chroma|pinecone`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `STUDYBUDDY_MEMORY_BUCKET`

## Deployment

AWS deployment currently uses:

- Lambda container image
- ECR
- API Gateway HTTP API
- S3 + CloudFront
- Terraform

Normal deploy flow:

```bash
cd terraform
terraform apply
```

The CI/CD workflow also deploys on push using GitHub Actions.

## Notes

- Local streaming works well; AWS may buffer responses depending on the current Lambda/API Gateway path.
- Upload transitions to chat only after successful ingestion/indexing.
- Memory is stored locally first, then synced to S3.
- The current `/upload` API path is best for smaller files; larger files should eventually move to direct-to-S3 upload plus async ingestion.
