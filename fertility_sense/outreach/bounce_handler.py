"""Bounce and unsubscribe detection -- monitors IMAP for bounces and unsubscribe requests."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

UNSUBSCRIBE_PATTERNS = [
    r"\bunsubscribe\b",
    r"\bremove me\b",
    r"\bstop sending\b",
    r"\bopt.?out\b",
    r"\bno more emails?\b",
]

BOUNCE_SUBJECTS = [
    r"undeliverable",
    r"delivery.?fail",
    r"mail.?delivery.?fail",
    r"returned mail",
    r"MAILER.?DAEMON",
]


class BounceHandler:
    def __init__(self, config):
        self.config = config
        self._unsub_patterns = [re.compile(p, re.IGNORECASE) for p in UNSUBSCRIBE_PATTERNS]
        self._bounce_patterns = [re.compile(p, re.IGNORECASE) for p in BOUNCE_SUBJECTS]

    def check_inbox_for_bounces(self) -> dict:
        """Check IMAP inbox for bounce and unsubscribe messages.
        Returns: {"unsubscribes": [...emails], "bounces": [...emails], "processed": int}
        """
        from fertility_sense.outreach.email_sender import EmailSender

        sender = EmailSender(self.config)
        messages = sender.check_inbox(limit=50)

        unsubscribes = []
        bounces = []

        for msg in messages:
            # Check for unsubscribe keywords in subject
            if any(p.search(msg.subject) for p in self._unsub_patterns):
                # Extract the sender's email as the one to unsubscribe
                unsubscribes.append(msg.from_addr)
                continue

            # Check for bounce
            if any(p.search(msg.subject) for p in self._bounce_patterns):
                # Try to extract the original recipient from subject/body
                bounces.append(msg.from_addr)

        return {
            "unsubscribes": unsubscribes,
            "bounces": bounces,
            "processed": len(messages),
        }

    def process_unsubscribes(self, emails: list[str]) -> int:
        """Mark prospects as unsubscribed in sequence engine."""
        from fertility_sense.outreach.sequences import SequenceEngine

        engine = SequenceEngine(
            sequences_dir=self.config.base_dir / "data" / "sequences",
            state_dir=self.config.data_dir / "outreach" / "sequence_state",
        )

        count = 0
        for email in emails:
            try:
                engine.unsubscribe(email)
                logger.info("Unsubscribed %s", email)
                count += 1
            except Exception:
                pass
        return count
