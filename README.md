# Vakil Yantra

Complete repository containing both the **Backend API** (FastAPI) and the **Frontend Web App** (Next.js) for Vakil Yantra.

## Project Structure

```
vakil-yantra/
├── backend/                  # FastAPI Python backend
│   ├── api/                  # Vercel serverless entrypoint
│   ├── app/                  # Application code (auth, matters, ai, etc.)
│   ├── migrations/           # Database schema & PostgreSQL RLS
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── vercel.json
├── web/                      # Next.js 14 frontend
│   ├── src/
│   │   ├── app/              # Next.js App Router (page, layout, styles)
│   │   ├── data/             # Curated legal acts, plans, tiers
│   │   └── lib/              # Typed API client
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.mjs
└── README.md
```

## Quick Start

### 1. Start the Backend API (Port 8000)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start the Frontend Web App (Port 3000)

```bash
cd web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.
