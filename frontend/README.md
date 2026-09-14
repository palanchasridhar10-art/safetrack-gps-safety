# SafeTrack Frontend (HTML / CSS / JS)

Plain HTML/CSS/JavaScript — no build step required.

## Run locally

Serve the folder with any static server (opening `index.html` directly via
`file://` will break the Geolocation API on most browsers, which requires a
secure context). Easiest options:

```bash
# Option 1: Python
cd frontend
python -m http.server 5500

# Option 2: VS Code "Live Server" extension
```

Then open `http://127.0.0.1:5500`.

## Point at your backend

By default the frontend talks to `http://127.0.0.1:8000` (the local FastAPI
dev server). To change this — e.g. for a deployed backend — add before the
`api.js` script tag in each HTML page:

```html
<script>window.SAFETRACK_API_BASE_URL = "https://your-backend.example.com";</script>
<script src="js/api.js"></script>
```

## Pages

| Page             | Purpose                                      |
|------------------|-----------------------------------------------|
| `index.html`     | Login (email + password)                      |
| `register.html`  | Create account                                 |
| `otp.html`       | Enter the emailed 6-digit OTP                  |
| `contacts.html`  | Add/remove the two required trusted contacts   |
| `dashboard.html` | Safety dashboard: SOS, send location, tracking |

## Notes on HTTPS

The browser Geolocation API requires a secure context (`https://` or
`localhost`) in production. Deploy the frontend behind HTTPS (e.g. Vercel,
Netlify, or any static host with TLS).
