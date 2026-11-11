from app.models.user import AccountStatus, User


def is_active_account(user: User) -> bool:
    """Treat legacy rows without a status as active when is_active is true."""

    return bool(getattr(user, "is_active", False)) and getattr(
        user,
        "status",
        None,
    ) in (None, AccountStatus.ACTIVE.value)
