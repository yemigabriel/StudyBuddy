# AGENTS.md

## Purpose

This repository contains a full-stack AI application called **StudyBuddy**.

Goal:
Build a simple, working RAG system with:

* FastAPI backend (Lambda-ready)
* Next.js frontend (S3 static hosting)
* S3-based conversation memory
* Terraform infrastructure
* GitHub Actions CI

Focus on:

* Simplicity
* Working end-to-end
* Clear structure

---

## Architecture Overview

Frontend:

* Next.js (TypeScript, Tailwind)
* Deployed to S3
* Served via CloudFront

Backend:

* FastAPI
* AWS Lambda (via Mangum)
* API Gateway exposure

Storage:

* S3 (frontend hosting)
* S3 (chat memory JSON)

---

## Core Features

### 1. RAG

* Document ingestion (pdf, docx, md)
* Chunking
* Embeddings (OpenAI)
* Vector store (Chromadb for local, Pinecone for production)
* Retrieval
* LLM response

### 2. Chat API

POST /chat:

* message
* session_id

Returns:

* response
* updates memory

### 3. Memory (IMPORTANT)

Store conversations as JSON:

[
{
"role": "user",
"content": "...",
"timestamp": "ISO_TIMESTAMP"
},
{
"role": "assistant",
"content": "...",
"timestamp": "ISO_TIMESTAMP"
}
]

Rules:

* Save locally first
* Save locally in /memory
* Upload to S3 using boto3
* Retrieve if session_id exists
* Use one S3 bucket for memory storage.
* Each session should be stored as:
memory/{session_id}.json

---

## Backend Rules

* Use FastAPI
* Use Mangum for Lambda compatibility
* Keep endpoints minimal:

  * POST /upload
  * POST /chat
  * GET /health
* Use boto3 for S3
* Keep logic simple and modular

---

## Frontend Rules

* Minimal UI:

  * Upload
  * Chat input
  * Response display
* Tailwind styling only
* No over-design

---

## Python Environment (uv)

Use uv instead of pip.

Commands:

* uv venv
* source .venv/bin/activate
* uv pip install -r requirements.txt

DO NOT use pip directly.

---

## Docker

* One Dockerfile (backend)
* Used for local development only
+ Not used for Lambda deployment
* Must run FastAPI successfully

---

## Terraform

Keep SIMPLE.

Must include:

* S3 (frontend)
* S3 (memory)
* Lambda
* IAM role (S3 access)
* API Gateway
* CloudFront

No complex modules.

---

## CI (GitHub Actions)

* Run on push
* Install dependencies
* Build backend
* Build Docker image

---

## Deployment

Backend:

* deploy.py handles packaging + Lambda upload

Frontend:

* Build → upload to S3

CORS:

* Allow CloudFront domain

---

## Git Commit Rules

* Initialize repo
* Branch: feature/ai-capstone

Commit after each step:

* scaffold
* backend
* frontend
* RAG
* memory
* Docker
* Terraform
* CI

Format:

* feat:
* chore:
* infra:
* ci:

Rules:

* One logical change per commit
* No mixed concerns
* Code must run before commit

---

## .gitignore Rules

Ignore:

Python:

* **pycache**/
* *.pyc
* .venv/

Node:

* node_modules/
* .next/

Env:

* .env*
* *.pem
* *.key

Terraform:

* .terraform/
* *.tfstate*

General:

* .DS_Store
* .vscode/

Never commit secrets.

---

## Constraints

* Time-boxed project
* Prefer working prototype over perfection
* Avoid over-engineering
* Add possible suggestions/improvements as TODO comments 

---

## Folder structure

/StudyBuddy
  /backend
    deploy.py
    main.py
  /frontend
  /memory
  /terraform
  docker-compose.yml (minimal)
  README.md

---

## Success Criteria

Project must:

* Run locally
* Support RAG
* Save memory to S3
* Be containerized
* Include Terraform
* Include CI workflow
* Be deployable (even if simplified)

---

## Final Note

Prioritize:

* clarity
* completeness
* execution speed
