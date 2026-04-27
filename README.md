# StudyBuddy

StudyBuddy is a simple full-stack AI app with:

- FastAPI backend
- Next.js frontend
- S3-backed memory
- Minimal Terraform infrastructure

## Local Development

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn server:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
