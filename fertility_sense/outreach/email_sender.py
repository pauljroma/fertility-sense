"""Email distribution — sends campaign content via IONOS SMTP.

Supports:
- Single email sends
- Batch sends with rate limiting
- HTML + plain text multipart
- IMAP inbox checking for replies/engagement
"""

from __future__ import annotations

import imaplib
import logging
import smtplib
import time
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from fertility_sense.config import FertilitySenseConfig

logger = logging.getLogger(__name__)

# Rate limit: max 10 emails per minute to avoid IONOS throttling
_MAX_EMAILS_PER_MINUTE = 10
_DELAY_BETWEEN_SENDS = 6.0  # seconds


@dataclass
class EmailMessage:
    """A single email ready to send."""
    to: str
    subject: str
    body_text: str
    body_html: str = ""
    reply_to: str = ""
    tags: list[str] = field(default_factory=list)
    campaign_id: str = ""
    topic_id: str = ""


@dataclass
class SendResult:
    """Result of an email send attempt."""
    to: str
    subject: str
    status: str  # "sent", "failed", "skipped"
    error: str | None = None
    sent_at: datetime | None = None
    message_id: str | None = None


@dataclass
class InboxMessage:
    """An email from the inbox (for engagement tracking)."""
    from_addr: str
    subject: str
    date: str
    uid: str
    snippet: str = ""


class EmailSender:
    """SMTP email sender with IONOS configuration."""

    def __init__(self, config: FertilitySenseConfig) -> None:
        self._config = config
        self._send_count = 0
        self._last_send_time = 0.0
        self._validate_config()

    def _validate_config(self) -> None:
        if not self._config.email_address:
            raise ValueError(
                "Email address is required. Set FERTILITY_SENSE_EMAIL_ADDRESS in .env"
            )
        if not self._config.email_password:
            raise ValueError(
                "Email password is required. Set FERTILITY_SENSE_EMAIL_PASSWORD in .env"
            )

    def test_connection(self) -> bool:
        """Test SMTP connection. Returns True if successful."""
        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(self._config.email_address, self._config.email_password)
                logger.info("SMTP connection test successful: %s", self._config.smtp_host)
                return True
        except Exception as e:
            logger.error("SMTP connection test failed: %s", e)
            return False

    def send(self, message: EmailMessage) -> SendResult:
        """Send a single email via SMTP."""
        self._rate_limit()

        msg = self._build_mime(message)
        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(self._config.email_address, self._config.email_password)
                smtp.send_message(msg)

            logger.info("Email sent to %s: %s", message.to, message.subject)
            return SendResult(
                to=message.to,
                subject=message.subject,
                status="sent",
                sent_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error("Failed to send email to %s: %s", message.to, e)
            return SendResult(
                to=message.to,
                subject=message.subject,
                status="failed",
                error=str(e),
            )

    def send_batch(self, messages: list[EmailMessage]) -> list[SendResult]:
        """Send multiple emails with rate limiting."""
        results = []
        for msg in messages:
            result = self.send(msg)
            results.append(result)
            if result.status == "sent":
                time.sleep(_DELAY_BETWEEN_SENDS)
        return results

    def check_inbox(self, folder: str = "INBOX", limit: int = 20) -> list[InboxMessage]:
        """Check inbox for replies/engagement via IMAP."""
        messages = []
        try:
            with imaplib.IMAP4_SSL(self._config.imap_host, self._config.imap_port) as imap:
                imap.login(self._config.email_address, self._config.email_password)
                imap.select(folder)
                _, data = imap.search(None, "ALL")
                uids = data[0].split()

                # Get latest N
                for uid in uids[-limit:]:
                    _, msg_data = imap.fetch(uid, "(RFC822.HEADER)")
                    if msg_data[0] is None:
                        continue
                    raw = msg_data[0][1]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")

                    # Parse basic headers
                    from_addr = _extract_header(raw, "From")
                    subject = _extract_header(raw, "Subject")
                    date = _extract_header(raw, "Date")

                    messages.append(InboxMessage(
                        from_addr=from_addr,
                        subject=subject,
                        date=date,
                        uid=uid.decode() if isinstance(uid, bytes) else str(uid),
                    ))
        except Exception as e:
            logger.error("IMAP check failed: %s", e)

        return messages

    def _build_mime(self, message: EmailMessage) -> MIMEMultipart:
        """Build a MIME multipart email."""
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self._config.email_from_name} <{self._config.email_address}>"
        msg["To"] = message.to
        msg["Subject"] = message.subject
        if message.reply_to:
            msg["Reply-To"] = message.reply_to

        # Plain text part
        msg.attach(MIMEText(message.body_text, "plain"))

        # HTML part (if provided)
        if message.body_html:
            msg.attach(MIMEText(message.body_html, "html"))

        return msg

    def _rate_limit(self) -> None:
        """Simple rate limiter to avoid IONOS throttling."""
        now = time.monotonic()
        if now - self._last_send_time < _DELAY_BETWEEN_SENDS:
            sleep_time = _DELAY_BETWEEN_SENDS - (now - self._last_send_time)
            time.sleep(sleep_time)
        self._last_send_time = time.monotonic()


def _extract_header(raw_headers: str, header_name: str) -> str:
    """Extract a header value from raw email headers."""
    for line in raw_headers.split("\n"):
        if line.lower().startswith(f"{header_name.lower()}:"):
            return line.split(":", 1)[1].strip()
    return ""


def campaign_to_email(
    to: str,
    subject: str,
    body: str,
    topic_id: str = "",
    campaign_id: str = "",
) -> EmailMessage:
    """Convert campaign content into an EmailMessage."""
    # Build simple HTML version
    html_body = f"""<html>
<body style="font-family: Arial, Helvetica, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
<div style="border-bottom: 3px solid #f5a623; padding-bottom: 15px; margin-bottom: 20px;">
    <strong style="color: #1a4d8c; font-size: 18px;">WIN Fertility</strong>
</div>

{_text_to_html(body)}

<div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; font-size: 12px; color: #999;">
    <p>WIN Fertility manages fertility benefits for leading employers including Disney, Nvidia, and JPM.</p>
    <p>Reply to this email to start a conversation with our enterprise team.</p>
</div>
</body>
</html>"""

    return EmailMessage(
        to=to,
        subject=subject,
        body_text=body,
        body_html=html_body,
        topic_id=topic_id,
        campaign_id=campaign_id,
    )


def _text_to_html(text: str) -> str:
    """Convert plain text to basic HTML paragraphs."""
    paragraphs = text.strip().split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Handle markdown-ish headers
        if p.startswith("## "):
            html_parts.append(f'<h2 style="color: #1a4d8c;">{p[3:]}</h2>')
        elif p.startswith("# "):
            html_parts.append(f'<h1 style="color: #1a4d8c;">{p[2:]}</h1>')
        elif p.startswith("- "):
            items = p.split("\n")
            html_parts.append("<ul>" + "".join(f"<li>{i.lstrip('- ')}</li>" for i in items) + "</ul>")
        else:
            # Bold markers
            p = p.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            html_parts.append(f"<p>{p}</p>")
    return "\n".join(html_parts)
