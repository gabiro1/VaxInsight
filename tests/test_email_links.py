from datetime import UTC, datetime

from app.api.routes.auth import invitation_landing_page
from app.core.config import settings
from app.services import email as email_service


def test_mobile_action_url_uses_the_configured_app_scheme(monkeypatch):
    monkeypatch.setattr(settings, "MOBILE_DEEP_LINK_BASE_URL", "vaxinsight://")

    assert (
        email_service._mobile_action_url("reset-password", "token/with space")
        == "vaxinsight://reset-password/token%2Fwith%20space"
    )


def test_invitation_landing_page_contains_a_clickable_mobile_handoff(monkeypatch):
    monkeypatch.setattr(
        settings,
        "MOBILE_DEEP_LINK_BASE_URL",
        "exp://192.168.1.20:8081/--",
    )

    response = invitation_landing_page("i" * 32)

    assert response.status_code == 200
    body = response.body.decode()
    assert 'href="exp://192.168.1.20:8081/--/invite/' in body
    assert "Cache-Control" in response.headers


def test_account_emails_include_mobile_action_links(monkeypatch):
    monkeypatch.setattr(settings, "ACCOUNT_ACTION_BASE_URL", "https://app.test/account")
    monkeypatch.setattr(settings, "MOBILE_DEEP_LINK_BASE_URL", "vaxinsight://")
    messages = []
    html_messages = []
    monkeypatch.setattr(
        email_service,
        "_send_email",
        lambda recipient, subject, body, **kwargs: (
            messages.append(body),
            html_messages.append(kwargs.get("html_body")),
        ),
    )
    expires_at = datetime.now(UTC)

    email_service.send_invitation_email("person@example.com", "invite-token", expires_at, "chw")
    email_service.send_password_reset_email("person@example.com", "reset-token", expires_at)
    email_service.send_email_verification_email("person@example.com", "123456", expires_at)

    assert "vaxinsight://invite/invite-token" in messages[0]
    assert 'href="vaxinsight://invite/invite-token"' in html_messages[0]
    assert "vaxinsight://reset-password/reset-token" in messages[1]
    assert "123456" in messages[2]
    assert "expires" in messages[2]


def test_account_emails_do_not_emit_an_unconfigured_browser_placeholder(monkeypatch):
    monkeypatch.setattr(settings, "ACCOUNT_ACTION_BASE_URL", None)
    monkeypatch.setattr(settings, "MOBILE_DEEP_LINK_BASE_URL", "vaxinsight://")
    messages = []
    html_messages = []
    monkeypatch.setattr(
        email_service,
        "_send_email",
        lambda recipient, subject, body, **kwargs: (
            messages.append(body),
            html_messages.append(kwargs.get("html_body")),
        ),
    )

    email_service.send_invitation_email(
        "person@example.com",
        "invite-token",
        datetime.now(UTC),
        "reviewer",
    )

    assert "app.example.invalid" not in messages[0]
    assert "Complete registration in a browser here" not in messages[0]
    assert "Open in the VaxInsight mobile app: vaxinsight://invite/invite-token" in messages[0]
    assert 'href="vaxinsight://invite/invite-token"' in html_messages[0]
