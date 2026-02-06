import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def is_truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_recipients(value: str) -> List[str]:
    if not value:
        return []
    parts: List[str] = []
    for token in str(value).replace(";", ",").split(","):
        token = token.strip()
        if token:
            parts.append(token)
    return parts


def build_execution_summary_table(durations: Dict[str, float]) -> Tuple[str, str]:
    if not durations:
        text = "No execution summary available."
        html = "<p>No execution summary available.</p>"
        return text, html

    rows = sorted(durations.items(), key=lambda item: item[0])
    header_step = "Step"
    header_duration = "Duration(s)"
    step_width = max(len(header_step), max(len(name) for name, _ in rows))
    duration_width = max(len(header_duration), max(len(f"{secs:.1f}") for _, secs in rows))

    text_lines = [
        f"{header_step:<{step_width}}  {header_duration:>{duration_width}}",
        f"{'-' * step_width}  {'-' * duration_width}",
    ]
    for name, secs in rows:
        text_lines.append(f"{name:<{step_width}}  {secs:>{duration_width}.1f}")
    text = "\n".join(text_lines)

    html_lines = [
        "<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">",
        "<thead><tr><th>Step</th><th>Duration (s)</th></tr></thead>",
        "<tbody>",
    ]
    for name, secs in rows:
        html_lines.append(f"<tr><td>{name}</td><td>{secs:.1f}</td></tr>")
    html_lines.append("</tbody></table>")
    html = "\n".join(html_lines)
    return text, html


def _smtp_connection(conf: Dict[str, str]) -> smtplib.SMTP:
    server = conf.get("SMTP_SERVER", "").strip()
    if not server:
        raise ValueError("Missing SMTP_SERVER in carto.conf")
    port = int(conf.get("SMTP_PORT", "25") or 25)
    timeout = float(conf.get("SMTP_TIMEOUT", "10") or 10)
    use_ssl = is_truthy(conf.get("SMTP_USE_SSL", ""))
    if use_ssl:
        return smtplib.SMTP_SSL(server, port, timeout=timeout)
    return smtplib.SMTP(server, port, timeout=timeout)


def send_carto_notification(
    conf: Dict[str, str],
    recipients: Iterable[str],
    subject: str,
    body_text: str,
    body_html: str,
    attachment_path: Path,
    logger,
) -> None:
    recipients = [r for r in recipients if r]
    if not recipients:
        raise ValueError("No email recipients provided")

    from_addr = conf.get("SMTP_FROM", "").strip() or recipients[0]
    reply_to = conf.get("SMTP_REPLY_TO", "").strip()
    username = conf.get("SMTP_USER", "").strip()
    password = conf.get("SMTP_PASSWORD", "").strip()
    use_tls = is_truthy(conf.get("SMTP_USE_TLS", ""))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    attachment_path = Path(attachment_path)
    if attachment_path.exists():
        msg.add_attachment(
            attachment_path.read_bytes(),
            maintype="text",
            subtype="plain",
            filename=attachment_path.name,
        )

    try:
        with _smtp_connection(conf) as server:
            if use_tls and not isinstance(server, smtplib.SMTP_SSL):
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
        logger.info("Notification email sent to %s", recipients)
    except Exception:
        logger.exception("Failed to send notification email")
        raise
