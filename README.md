# SafeTrack — GPS Safety & Family Location Alert System

A consent-based personal safety web app. A user logs in (email + password +
email OTP), adds exactly two trusted contacts, and can then share her
current GPS location with them via WhatsApp, run live safety tracking while
she's on the move, or trigger an Emergency SOS — all only when she chooses
to. Nothing is tracked or sent silently.

```
Login → OTP Verification → Add 2 Trusted Contacts → Enable GPS → Share Location → WhatsApp Alert
```

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite (swap-in PostgreSQL for production), JWT auth, bcrypt password/OTP hashing, WhatsApp Business Cloud API (falls back to `wa.me` click-to-chat links if unconfigured)
- **Frontend:** Plain HTML, CSS, JavaScript (no framework/build step) — browser Geolocation API

## Quick start

**1. Backend**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then edit JWT_SECRET at minimum
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (in a second terminal)

```bash
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`, register an account, log in, and — since no
SMTP server is configured by default — read the OTP straight off the page
(dev-mode preview) or the backend terminal.

## Project structure

```
safetrack/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router mounting
│   │   ├── config.py          # env-driven settings
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── deps.py            # auth guard + rate limiter
│   │   ├── models/            # ORM models (users, contacts, OTP, locations, sessions, SOS)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── security/          # password hashing, JWT issuing
│   │   ├── services/          # email, OTP, WhatsApp business logic
│   │   └── routers/           # /api/auth, /contacts, /location, /safety, /emergency
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html             # login
│   ├── register.html
│   ├── otp.html
│   ├── contacts.html
│   ├── dashboard.html         # SOS, send location, live tracking
│   ├── css/style.css
│   └── js/                    # api.js, geo.js, per-page logic
│
└── README.md (this file)
```

## Security & privacy, by design

- Passwords and OTPs are bcrypt-hashed — never stored or logged in plain text.
- Login requires both password **and** a single-use, 5-minute email OTP.
- Every location/SOS/contact endpoint requires a valid bearer token and is scoped to the authenticated user's own records only.
- Location sharing and tracking require an explicit user action each time; the dashboard shows a consent notice before either starts.
- Login, OTP verification, and SOS endpoints are rate-limited to slow brute-force/abuse attempts.
- Trusted contacts are capped at exactly two, with phone numbers validated and normalized to E.164.
- WhatsApp messages go through the official Business Cloud API when configured, or open a pre-filled `wa.me` link the user taps herself — never automation of a personal WhatsApp account.

## Known limitations (see the architecture doc for detail)

- Live tracking (Mode B) uses the browser Geolocation `watchPosition` API, which pauses when the tab/browser is closed or backgrounded on mobile OSes. True background tracking would require a native app.
- The WhatsApp Cloud API's free-form messaging only works inside a 24-hour customer-service window; outside it, an approved message **template** is required — swap this in before going to production (see `services/whatsapp_service.py`).
- This is an MVP/prototype: add HTTPS, PostgreSQL + Alembic migrations, and a proper email provider (SendGrid/SES/Resend) before any real deployment.

## Priority order (per the design brief)

**Safety → Consent → Privacy → Security → Reliability → Usability → UI**
