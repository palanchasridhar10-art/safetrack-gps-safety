"""
Email delivery service.

Sends the OTP email over SMTP when credentials are configured. In local
development (no SMTP_HOST set), it logs to the console instead so the auth
flow can be tested without a mail server — the OTP is never written to a
persistent log file, only shown once in the terminal.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("safetrack.email")


def send_otp_email(to_email: str, otp: str, expires_minutes: int) -> None:
    subject = "Your SafeTrack login code"
    body = (
        f"Your SafeTrack one-time login code is: {otp}\n\n"
        f"This code expires in {expires_minutes} minutes and can only be used once.\n"
        f"If you did not request this, you can safely ignore this email."
    )

    if not settings.SMTP_HOST:
        # Dev fallback — never used in production once SMTP_* is configured.
        logger.info("[DEV EMAIL] To: %s | Subject: %s | OTP not logged for safety.", to_email, subject)
        print(f"\n[DEV MODE] OTP email to {to_email}: {otp} (expires in {expires_minutes}m)\n")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
