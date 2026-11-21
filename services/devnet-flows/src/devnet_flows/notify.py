import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from devnet_config import get_config
from devnet_config.models import MailConfig
from devnet_core.exceptions import SystemConnectionError
from devnet_core.logging import get_logger

logger = get_logger(__name__)

# Seconds for each step of the SMTP session
TIMEOUT = 30


async def mail_report(summary: str, markdown: str) -> None:
    """
    Mail a run report to the recipients of `mail` in devnet.yaml. Without `mail`, the log says the report is not sent

    Args:
        summary: The subject, e.g. "ingest-devices: 120 devices, 117 done, 3 failed, 5 need attention"
        markdown: The body

    Raises:
        SystemConnectionError: If the SMTP server can't be reached or refuses the mail
    """
    config = get_config().mail
    if config is None:
        logger.warning(f"mail is not configured, the report is not sent: {summary}")
        return

    message = EmailMessage()
    message["Subject"] = summary
    message["From"] = config.sender
    message["To"] = ", ".join(config.to)
    message.set_content(markdown)

    # smtplib blocks the event loop
    await asyncio.to_thread(_send, config, message)
    logger.info(f"report mailed to {message['To']}")


def _send(config: MailConfig, message: EmailMessage) -> None:
    context = ssl.create_default_context()
    if not config.verify_tls:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    try:
        if config.security == "tls":
            smtp: smtplib.SMTP = smtplib.SMTP_SSL(config.host, config.port, timeout=TIMEOUT, context=context)
        else:
            smtp = smtplib.SMTP(config.host, config.port, timeout=TIMEOUT)
        with smtp:
            if config.security == "starttls":
                smtp.starttls(context=context)
            if config.username is not None and config.password is not None:
                smtp.login(config.username.get_secret_value(), config.password.get_secret_value())
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as e:
        raise SystemConnectionError("mail", str(e)) from e
