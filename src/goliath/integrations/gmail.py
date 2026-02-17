"""
Gmail Integration — send emails via Gmail SMTP.

SETUP INSTRUCTIONS
==================

1. Go to your Google Account > Security > 2-Step Verification.
   Make sure 2-Step Verification is enabled.

2. Go to https://myaccount.google.com/apppasswords

3. Generate an App Password:
   - Select app: "Mail"
   - Select device: "Other" (enter "GOLIATH")
   - Click Generate — you'll get a 16-character password.

4. Add these to your .env file:
     GMAIL_ADDRESS=yourname@gmail.com
     GMAIL_APP_PASSWORD=abcd efgh ijkl mnop

   The app password works with spaces or without — either is fine.

IMPORTANT NOTES
===============
- This uses SMTP (smtp.gmail.com:587 with STARTTLS), not the Gmail API.
  No OAuth setup, no Google Cloud project needed.
- App Passwords only work with 2-Step Verification enabled.
- For Google Workspace accounts, your admin may need to allow
  "Less secure app" access or App Passwords.
- Attachment size limit is ~25 MB (Gmail's standard limit).

Usage:
    from goliath.integrations.gmail import GmailClient

    gm = GmailClient()

    # Simple email
    gm.send(
        to="someone@example.com",
        subject="Hello from GOLIATH",
        body="This email was sent by the GOLIATH automation engine.",
    )

    # HTML email
    gm.send(
        to="someone@example.com",
        subject="Report Ready",
        body="<h1>Report</h1><p>Your report is ready.</p>",
        html=True,
    )

    # Email with attachments
    gm.send(
        to="someone@example.com",
        subject="Files attached",
        body="See attached.",
        attachments=["report.pdf", "data.csv"],
    )

    # Multiple recipients
    gm.send(
        to=["alice@example.com", "bob@example.com"],
        subject="Team update",
        body="New deployment is live.",
    )
"""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from goliath import config

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


class GmailClient:
    """Gmail SMTP client for sending emails with optional attachments."""

    def __init__(self):
        if not config.GMAIL_ADDRESS:
            raise RuntimeError(
                "GMAIL_ADDRESS is not set. "
                "Add it to .env or export as an environment variable."
            )
        if not config.GMAIL_APP_PASSWORD:
            raise RuntimeError(
                "GMAIL_APP_PASSWORD is not set. "
                "Generate one at https://myaccount.google.com/apppasswords "
                "and add it to .env."
            )
        self.address = config.GMAIL_ADDRESS
        self.password = config.GMAIL_APP_PASSWORD

    # -- public API --------------------------------------------------------

    def send(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: bool = False,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        attachments: list[str] | None = None,
    ) -> None:
        """Send an email via Gmail SMTP.

        Args:
            to:          Recipient address or list of addresses.
            subject:     Email subject line.
            body:        Email body (plain text or HTML).
            html:        If True, body is treated as HTML.
            cc:          CC recipients.
            bcc:         BCC recipients.
            attachments: List of file paths to attach.
        """
        to_list = [to] if isinstance(to, str) else list(to)
        cc_list = [cc] if isinstance(cc, str) else list(cc or [])
        bcc_list = [bcc] if isinstance(bcc, str) else list(bcc or [])

        msg = MIMEMultipart()
        msg["From"] = self.address
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = subject
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)

        # Body
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))

        # Attachments
        for file_path in attachments or []:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Attachment not found: {file_path}")
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), Name=path.name)
            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(part)

        # Send
        all_recipients = to_list + cc_list + bcc_list
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.starttls()
            server.login(self.address, self.password)
            server.sendmail(self.address, all_recipients, msg.as_string())
