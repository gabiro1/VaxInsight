import smtplib
from datetime import datetime
from email.message import EmailMessage
from html import escape
from urllib.parse import quote

from app.core.config import settings


class EmailDeliveryError(Exception):
    """Raised when an account email cannot be delivered."""


def _web_action_url(route: str, token: str) -> str | None:
    if not settings.ACCOUNT_ACTION_BASE_URL:
        return None
    return (
        f"{settings.ACCOUNT_ACTION_BASE_URL.rstrip('/')}/{route}"
        f"?token={quote(token, safe='')}"
    )


def _mobile_action_url(route: str, token: str) -> str | None:
    return mobile_action_url(route, token)


def mobile_action_url(route: str, token: str) -> str | None:
    base_url = settings.MOBILE_DEEP_LINK_BASE_URL
    if not base_url:
        return None
    separator = "" if base_url.endswith("://") else "/"
    return f"{base_url}{separator}{route}/{quote(token, safe='')}"


def _action_link_lines(
    web_route: str,
    mobile_route: str,
    token: str,
    web_label: str,
) -> str:
    return "\n".join(
        f"{label}: {url}"
        for label, url in _action_links(web_route, mobile_route, token, web_label)
    )


def _action_links(
    web_route: str,
    mobile_route: str,
    token: str,
    web_label: str,
) -> list[tuple[str, str]]:
    links = []
    web_url = _web_action_url(web_route, token)
    if web_url:
        links.append((web_label, web_url))
    mobile_url = _mobile_action_url(mobile_route, token)
    if mobile_url:
        links.append(("Open in the VaxInsight mobile app", mobile_url))
    return links


def _action_links_html(
    web_route: str,
    mobile_route: str,
    token: str,
    web_label: str,
) -> str:
    return "".join(
        f'<p><a href="{escape(url, quote=True)}">{escape(label)}</a></p>'
        for label, url in _action_links(web_route, mobile_route, token, web_label)
    )


def _send_email(
    recipient: str,
    subject: str,
    body: str,
    *,
    html_body: str | None = None,
) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise EmailDeliveryError("Email delivery is not configured")

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            smtp.ehlo()
            if settings.SMTP_USE_TLS:
                smtp.starttls()
                smtp.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError("Email delivery failed") from error


def send_invitation_email(
    recipient: str,
    token: str,
    expires_at: datetime,
    role: str,
) -> None:
    action_links = _action_link_lines(
        "accept-invitation",
        "invite",
        token,
        "Complete registration in a browser here",
    )
    action_links_html = _action_links_html(
        "accept-invitation",
        "invite",
        token,
        "Complete registration in a browser here",
    )
    body = (
        "You have been invited to create a VaxInsight account.\n\n"
        f"Role: {role}\n"
        f"{action_links}\n\n"
        f"This invitation expires at {expires_at.isoformat()} and can be used once."
    )
    html_body = (
        "<html><body>"
        "<p>You have been invited to create a VaxInsight account.</p>"
        f"<p><strong>Role:</strong> {escape(role)}</p>"
        f"{action_links_html}"
        f"<p>This invitation expires at {escape(expires_at.isoformat())} "
        "and can be used once.</p>"
        "</body></html>"
    )
    _send_email(
        recipient,
        "Your VaxInsight invitation",
        body,
        html_body=html_body,
    )


def send_password_reset_email(recipient: str, token: str, expires_at: datetime) -> None:
    action_links = _action_link_lines(
        "reset-password",
        "reset-password",
        token,
        "Reset your password in a browser here",
    )
    action_links_html = _action_links_html(
        "reset-password",
        "reset-password",
        token,
        "Reset your password in a browser here",
    )
    body = (
        "A VaxInsight password reset was requested for this email address.\n\n"
        f"{action_links}\n\n"
        f"This link expires at {expires_at.isoformat()} and can be used once."
    )
    html_body = (
        "<html><body>"
        "<p>A VaxInsight password reset was requested for this email address.</p>"
        f"{action_links_html}"
        f"<p>This link expires at {escape(expires_at.isoformat())} "
        "and can be used once.</p>"
        "</body></html>"
    )
    _send_email(
        recipient,
        "Reset your VaxInsight password",
        body,
        html_body=html_body,
    )


def send_email_verification_email(
    recipient: str,
    otp: str,
    expires_at: datetime,
) -> None:
    body = (
        "Your VaxInsight email verification code is:\n\n"
        f"{otp}\n\n"
        f"This code expires at {expires_at.isoformat()} and can be used once.\n"
        "Do not share this code with anyone."
    )
    _send_email(recipient, "Verify your VaxInsight email", body)
