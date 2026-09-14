# SafeTrack Backend (Python / FastAPI)

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `JWT_SECRET` — set a long random value (e.g. `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- `DATABASE_URL` — defaults to local SQLite; point at PostgreSQL for production
- `SMTP_*` — leave blank for local dev (OTP prints to the console instead); fill in for real email delivery
- `WHATSAPP_*` — leave blank to use `wa.me` click-to-chat links; fill in once you have an approved WhatsApp Business Cloud API account

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Notes

- **Dev-mode OTP**: with no `SMTP_HOST` set, `/api/auth/login` includes a `dev_otp_preview` field and the code is printed to the terminal, so you can test the full flow without a mail server. This is automatically disabled once `SMTP_HOST` is set or `ENVIRONMENT=production`.
- **WhatsApp**: without Cloud API credentials, the backend returns `wa.me` click-to-chat links — opening one pre-fills the alert message in WhatsApp, but a human still has to tap Send. No personal WhatsApp account is ever automated or scraped, per the project's architecture requirements.
- **Database**: tables are auto-created on startup for the SQLite prototype. For PostgreSQL in production, introduce Alembic migrations instead of relying on `create_all`.
- **Rate limiting**: login, OTP verification, and SOS endpoints are rate-limited per client IP (`slowapi`). Tune limits in `.env`.
