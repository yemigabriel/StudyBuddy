# StudyBuddy

StudyBuddy is a full-stack AI study assistant that turns uploaded documents into:

- chat answers
- summaries
- quizzes
- flashcards

It uses a RAG pipeline, OpenAI-powered agents, bucket-backed memory, and Terraform-managed cloud deployment.

## Screenshots

| Landing page | Chat | Quiz | Flashcards
|---|---|---|---|
| <img width="1413" height="720" alt="Screenshot 2026-04-27 at 22 52 51" src="https://github.com/user-attachments/assets/350cca84-8be6-4bfe-86b7-e29da65ee94f" /> | <img width="1010" height="718" alt="Screenshot 2026-04-27 at 23 07 58" src="https://github.com/user-attachments/assets/4751a954-9c9b-495d-865a-5822ffae5484" /> | <img width="1237" height="700" alt="Screenshot 2026-04-27 at 22 50 51" src="https://github.com/user-attachments/assets/50c6c5f6-f943-4b39-9365-4a828219d3c4" /> | <img width="1237" height="698" alt="Screenshot 2026-04-27 at 22 51 45" src="https://github.com/user-attachments/assets/8cba3ddf-4df3-4360-82ed-16921403afb9" /> |


## Architecture

```text
Frontend (Next.js static export on S3 + CloudFront, or Cloud Storage)
  -> Upload-files
  -> Sends chat / summary / quiz / flashcards requests
  -> Renders chat, quiz modal, and flashcards modal

Backend (FastAPI on AWS Lambda via Mangum, or Cloud Run)
  -> Parses documents
  -> Chunks content
  -> Retrieves context from vector store
  -> Calls OpenAI for QA or OpenAI Agents SDK for summary / quiz / flashcards
  -> Persists session memory locally + cloud object storage

Storage
  -> S3 or Cloud Storage frontend bucket
  -> S3 or Cloud Storage memory bucket
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
uv run pytest tests -q
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
- `MEMORY_BACKEND=local|s3|gcs`
- `STUDYBUDDY_MEMORY_BUCKET`

## Deployment

AWS deployment currently uses:

- Lambda container image
- ECR
- API Gateway HTTP API
- S3 + CloudFront
- Terraform

Normal AWS deploy flow:

```bash
cd terraform
terraform apply
```

Google Cloud deployment now uses:

- Cloud Run
- Artifact Registry
- Cloud Storage
- Terraform in `terraform/gcp`

Example GCP deploy flow:

```bash
cd backend
python3 deploy_gcp.py --image-uri us-central1-docker.pkg.dev/<project-id>/<repo>/studybuddy-backend:latest

cd ../terraform/gcp
terraform init -backend-config="bucket=<tf-state-bucket>" -backend-config="prefix=studybuddy"
terraform apply
```

The repository now includes:

- AWS workflow in `.github/workflows/ci.yml`
- GCP workflow in `.github/workflows/gcp.yml`

## Notes

- Local streaming works well; AWS may buffer responses depending on the current Lambda/API Gateway path.
- Cloud Run is the preferred Google Cloud target because it matches the existing backend container model with fewer code changes than Lambda.
- Upload transitions to chat only after successful ingestion/indexing.
- Memory is stored locally first, then synced to the configured object store.
- The current `/upload` API path is best for smaller files; larger files should eventually move to direct-to-S3 upload plus async ingestion.
