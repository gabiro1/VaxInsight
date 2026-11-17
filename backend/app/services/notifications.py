from __future__ import annotations

import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notifications import (
    NotificationDevice,
    NotificationFrequency,
    NotificationPreference,
)
from app.models.user import AccountStatus, User
from app.models.vaccine_content import VaccineContent, VaccineContentStatus

logger = logging.getLogger(__name__)

_EXPO_TOKEN_PATTERN = re.compile(
    r"^(?:ExponentPushToken|ExpoPushToken)\[[^\[\]\s]{1,240}\]$"
)
_COOLDOWNS = {
    NotificationFrequency.HOURLY.value: timedelta(hours=1),
    NotificationFrequency.DAILY.value: timedelta(days=1),
    NotificationFrequency.TWO_DAYS.value: timedelta(days=2),
    NotificationFrequency.MONTHLY.value: timedelta(days=30),
}
_INVALID_TOKEN_ERRORS = frozenset(
    {
        "DeviceNotRegistered",
        "InvalidCredentials",
        "InvalidPushToken",
        "InvalidToken",
    }
)
_MAX_EXPO_BATCH_SIZE = 100


class NotificationPersistenceError(Exception):
    """Raised when notification preferences or devices cannot be persisted."""


class ExpoPushError(Exception):
    """Raised when the Expo push endpoint cannot accept a request."""


def validate_expo_push_token(value: str) -> str:
    """Validate and normalize the two Expo token formats supported by this API."""

    if not isinstance(value, str):
        raise TypeError("token must be a string")

    normalized = value.strip()
    if len(normalized) > 255 or not _EXPO_TOKEN_PATTERN.fullmatch(normalized):
        raise ValueError(
            "token must use the ExponentPushToken[...] or ExpoPushToken[...] format"
        )
    return normalized


def cooldown_for_frequency(frequency: str | NotificationFrequency) -> timedelta:
    """Return the minimum interval between accepted notifications."""

    value = NotificationFrequency(frequency).value
    return _COOLDOWNS[value]


def is_notification_due(
    last_notified_at: datetime | None,
    frequency: str | NotificationFrequency,
    *,
    now: datetime | None = None,
) -> bool:
    """Check whether a user's preference cooldown has elapsed."""

    if last_notified_at is None:
        return True

    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    if last_notified_at.tzinfo is None:
        last_notified_at = last_notified_at.replace(tzinfo=UTC)

    return current_time - last_notified_at >= cooldown_for_frequency(frequency)


@dataclass(frozen=True)
class ExpoPushMessage:
    token: str
    title: str
    body: str
    data: dict[str, str] | None = None


@dataclass(frozen=True)
class ExpoPushResult:
    accepted_tokens: frozenset[str]
    invalid_tokens: frozenset[str]


class ExpoPushSender:
    """Small stdlib-only client for the Expo push endpoint."""

    def __init__(
        self,
        *,
        url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.url = url or settings.EXPO_PUSH_URL
        self.timeout = timeout or settings.EXPO_PUSH_TIMEOUT_SECONDS

    def send(self, messages: list[ExpoPushMessage]) -> ExpoPushResult:
        if not messages:
            return ExpoPushResult(frozenset(), frozenset())
        if len(messages) > _MAX_EXPO_BATCH_SIZE:
            raise ValueError("Expo push requests may contain at most 100 messages")

        payload = []
        for message in messages:
            item = {
                "to": message.token,
                "title": message.title,
                "body": message.body,
            }
            if message.data is not None:
                item["data"] = message.data
            payload.append(item)

        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status_code = response.status
                response_body = response.read()
        except HTTPError as error:
            raise ExpoPushError(
                f"Expo push endpoint returned HTTP {error.code}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise ExpoPushError("Expo push endpoint is unavailable") from error

        if not 200 <= status_code < 300:
            raise ExpoPushError("Expo push endpoint rejected the request")

        try:
            response_data = json.loads(response_body)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExpoPushError("Expo push endpoint returned invalid JSON") from error

        tickets = response_data.get("data") if isinstance(response_data, dict) else None
        if not isinstance(tickets, list) or len(tickets) != len(messages):
            raise ExpoPushError("Expo push endpoint returned an invalid ticket list")

        accepted_tokens: set[str] = set()
        invalid_tokens: set[str] = set()
        for message, ticket in zip(messages, tickets, strict=True):
            if not isinstance(ticket, dict):
                continue
            if ticket.get("status") == "ok":
                accepted_tokens.add(message.token)
            elif _ticket_error_code(ticket) in _INVALID_TOKEN_ERRORS:
                invalid_tokens.add(message.token)

        return ExpoPushResult(
            accepted_tokens=frozenset(accepted_tokens),
            invalid_tokens=frozenset(invalid_tokens),
        )


def _ticket_error_code(ticket: dict) -> str | None:
    details = ticket.get("details")
    if isinstance(details, dict) and details.get("error"):
        return str(details["error"])
    error = ticket.get("error")
    return str(error) if error else None


def get_or_create_notification_preferences(
    db: Session,
    *,
    user_id: UUID,
) -> NotificationPreference:
    try:
        preference = db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        if preference is not None:
            return preference

        preference = NotificationPreference(
            user_id=user_id,
            frequency=NotificationFrequency.DAILY.value,
        )
        db.add(preference)
        db.commit()
        db.refresh(preference)
        return preference
    except IntegrityError:
        db.rollback()
        preference = db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        if preference is not None:
            return preference
        raise NotificationPersistenceError from None
    except SQLAlchemyError as error:
        db.rollback()
        raise NotificationPersistenceError from error


def update_notification_preferences(
    db: Session,
    *,
    user_id: UUID,
    frequency: str | NotificationFrequency,
) -> NotificationPreference:
    try:
        normalized_frequency = NotificationFrequency(frequency).value
        preference = db.scalar(
            select(NotificationPreference)
            .where(NotificationPreference.user_id == user_id)
            .with_for_update()
        )
        if preference is None:
            preference = NotificationPreference(
                user_id=user_id,
                frequency=normalized_frequency,
            )
            db.add(preference)
        else:
            preference.frequency = normalized_frequency
        db.commit()
        db.refresh(preference)
        return preference
    except SQLAlchemyError as error:
        db.rollback()
        raise NotificationPersistenceError from error


def register_notification_device(
    db: Session,
    *,
    user_id: UUID,
    token: str,
    platform: str | None = None,
) -> NotificationDevice:
    normalized_token = validate_expo_push_token(token)
    now = datetime.now(UTC)

    try:
        device = db.scalar(
            select(NotificationDevice)
            .where(NotificationDevice.token == normalized_token)
            .with_for_update()
        )
        if device is None:
            device = NotificationDevice(
                user_id=user_id,
                token=normalized_token,
                platform=platform,
                last_seen_at=now,
            )
            db.add(device)
        else:
            # A device token follows the currently authenticated app account.
            device.user_id = user_id
            if platform is not None:
                device.platform = platform
            device.last_seen_at = now

        preference = db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        if preference is None:
            db.add(
                NotificationPreference(
                    user_id=user_id,
                    frequency=NotificationFrequency.DAILY.value,
                )
            )

        db.commit()
        db.refresh(device)
        return device
    except IntegrityError as error:
        db.rollback()
        raise NotificationPersistenceError from error
    except SQLAlchemyError as error:
        db.rollback()
        raise NotificationPersistenceError from error


def unregister_notification_device(
    db: Session,
    *,
    user_id: UUID,
    device_id: UUID,
) -> bool:
    try:
        device = db.scalar(
            select(NotificationDevice).where(
                NotificationDevice.id == device_id,
                NotificationDevice.user_id == user_id,
            )
        )
        if device is None:
            return False
        db.delete(device)
        db.commit()
        return True
    except SQLAlchemyError as error:
        db.rollback()
        raise NotificationPersistenceError from error


@dataclass
class _NotificationRecipient:
    preference: NotificationPreference | None
    devices: list[NotificationDevice]


@dataclass(frozen=True)
class NotificationDispatchResult:
    enabled: bool
    users_considered: int = 0
    users_notified: int = 0
    devices_removed: int = 0


def dispatch_new_vaccine_content_notification(
    db: Session,
    *,
    content: VaccineContent,
    sender: ExpoPushSender | None = None,
    now: datetime | None = None,
) -> NotificationDispatchResult:
    """Notify eligible active users without allowing provider failures to escape."""

    if content.status != VaccineContentStatus.PUBLISHED.value:
        return NotificationDispatchResult(enabled=False)
    if not settings.EXPO_PUSH_ENABLED or not settings.EXPO_PUSH_URL:
        return NotificationDispatchResult(enabled=False)

    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    push_sender = sender or ExpoPushSender()

    try:
        active_account = (
            and_(
                User.is_active.is_(True),
                or_(
                    User.status.is_(None),
                    User.status == AccountStatus.ACTIVE.value,
                ),
            )
        )
        rows = db.execute(
            select(NotificationDevice, NotificationPreference)
            .join(User, User.id == NotificationDevice.user_id)
            .outerjoin(
                NotificationPreference,
                NotificationPreference.user_id == NotificationDevice.user_id,
            )
            .where(active_account)
            .order_by(NotificationDevice.user_id, NotificationDevice.created_at)
        ).all()

        recipients: dict[UUID, _NotificationRecipient] = {}
        for device, preference in rows:
            recipient = recipients.setdefault(
                device.user_id,
                _NotificationRecipient(preference=preference, devices=[]),
            )
            recipient.devices.append(device)

        users_notified = 0
        devices_removed = 0
        for user_id, recipient in recipients.items():
            preference = db.scalar(
                select(NotificationPreference)
                .where(NotificationPreference.user_id == user_id)
                .with_for_update()
            )
            if preference is None:
                preference = NotificationPreference(
                    user_id=user_id,
                    frequency=NotificationFrequency.DAILY.value,
                )
                db.add(preference)
                db.flush()
                recipient.preference = preference

            if not is_notification_due(
                preference.last_notified_at,
                preference.frequency,
                now=current_time,
            ):
                continue

            accepted = False
            for start in range(0, len(recipient.devices), _MAX_EXPO_BATCH_SIZE):
                batch_devices = recipient.devices[start : start + _MAX_EXPO_BATCH_SIZE]
                batch_tokens = {device.token for device in batch_devices}
                messages = [
                    ExpoPushMessage(
                        token=device.token,
                        title=f"New vaccine information: {content.title}",
                        body=content.summary,
                        data={
                            "type": "vaccine_content",
                            "content_id": str(content.id),
                        },
                    )
                    for device in batch_devices
                ]
                try:
                    result = push_sender.send(messages)
                except Exception as error:  # noqa: BLE001
                    logger.warning(
                        "Expo push batch failed with %s",
                        type(error).__name__,
                    )
                    continue

                if result.accepted_tokens & batch_tokens:
                    accepted = True

                invalid_tokens = result.invalid_tokens & batch_tokens
                if invalid_tokens:
                    db.execute(
                        delete(NotificationDevice).where(
                            NotificationDevice.user_id == user_id,
                            NotificationDevice.token.in_(invalid_tokens),
                        )
                    )
                    devices_removed += len(invalid_tokens)

            if accepted:
                preference.last_notified_at = current_time
                users_notified += 1

        db.commit()
        return NotificationDispatchResult(
            enabled=True,
            users_considered=len(recipients),
            users_notified=users_notified,
            devices_removed=devices_removed,
        )
    except SQLAlchemyError as error:
        db.rollback()
        logger.warning(
            "Notification dispatch persistence failed with %s",
            type(error).__name__,
        )
        return NotificationDispatchResult(enabled=True)
