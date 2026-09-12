from email.message import EmailMessage
import logging
import smtplib

from app.core.config import settings

logger = logging.getLogger("vakil_yantra.email")


class EmailDeliveryError(RuntimeError):
    pass


def send_email(to_email: str, subject: str, text_body: str) -> str:
    if not settings.smtp_host:
        logger.warning("Email provider not configured. To=%s subject=%s body=%s", to_email, subject, text_body)
        return "console"

    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - depends on external SMTP
        raise EmailDeliveryError("Email delivery failed") from exc

    return "smtp"
