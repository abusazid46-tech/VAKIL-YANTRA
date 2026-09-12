# Vakil Yantra Backend

FastAPI backend foundation for the Vakil Yantra MVP.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Demo credentials:

```text
advocate@vakilyantra.in / Vakil@123
associate@vakilyantra.in / Associate@123
OTP: 123456
```

## Implemented structure

- Auth: login challenge, OTP verification, bearer token dependency.
- Tenant context: firm-aware current user model.
- Matters: list/create matter endpoints.
- Documents: signed upload intent and document listing stubs.
- Legal content: curated MVP corpus search.
- AI/RAG: drafting/case-analysis request shape with source-grounded response stubs.
- Limitation: deterministic calculation endpoint.
- Billing: plan list and Razorpay order/webhook placeholders.
- Audit: in-memory event recording shape.

## PostgreSQL / RLS

Local development defaults to SQLite for convenience:

```text
DATABASE_URL=sqlite:///./vakil_yantra_dev.db
```

Production should use PostgreSQL:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/vakil_yantra
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
AUTO_CREATE_DB=false
```

Apply the RLS baseline after tables are created:

```bash
psql "$DATABASE_URL" -f migrations/001_postgres_rls.sql
```

The application sets `app.current_firm_id` per request before tenant-owned queries. Tenant-owned tables include `matters`, `documents`, `ai_runs`, and `audit_events`.

## Frontend connection

Set this in `web/.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

The web login now calls:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/verify-otp`
- `GET /api/v1/auth/me`

Do not expose `SUPABASE_SERVICE_ROLE_KEY` to the frontend. Keep it backend-only for trusted server-side storage, administrative auth operations, and integrations.

## Production next steps

- Move from demo OTP to managed MFA or a real OTP delivery provider.
- Add refresh tokens / secure cookie sessions.
- Add Alembic migration generation instead of `create_all`.
- Replace signed URL stubs with S3/R2/Azure Blob.
- Add Celery/Dramatiq workers for OCR, exports, RAG ingestion, reminders, and billing reconciliation.
- Wire Razorpay signature validation and idempotent webhook processing.
