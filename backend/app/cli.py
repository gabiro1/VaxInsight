import argparse
from datetime import UTC, datetime
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models.user import AccountStatus, User, UserRole
from app.services.rate_limit_cleanup import (
    RateLimitCleanupError,
    cleanup_expired_rate_limit_buckets,
)

STAFF_ROLES = (UserRole.CHW.value, UserRole.REVIEWER.value)


def create_admin(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                is_active=True,
                status=AccountStatus.ACTIVE.value,
                role=UserRole.ADMINISTRATOR.value,
                email_verified_at=datetime.now(UTC),
                password_changed_at=datetime.now(UTC),
            )
            db.add(user)
        else:
            user.hashed_password = hash_password(password)
            user.is_active = True
            user.status = AccountStatus.ACTIVE.value
            user.role = UserRole.ADMINISTRATOR.value
            user.email_verified_at = datetime.now(UTC)
            user.password_changed_at = datetime.now(UTC)

        db.commit()
    finally:
        db.close()


def create_staff(
    email: str,
    *,
    full_name: str | None,
    role: str,
    password: str,
) -> None:
    """Provision an active, verified staff account without email delivery."""

    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == email)) is not None:
            raise ValueError(f"An account with {email} already exists.")

        now = datetime.now(UTC)
        db.add(
            User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                is_active=True,
                status=AccountStatus.ACTIVE.value,
                role=role,
                email_verified_at=now,
                password_changed_at=now,
            )
        )

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(f"An account with {email} already exists.") from None
    finally:
        db.close()


def cleanup_rate_limits(
    *,
    batch_size: int | None = None,
    max_batches: int | None = None,
) -> int:
    """Remove a bounded number of expired rate-limit buckets."""

    db = SessionLocal()
    try:
        return cleanup_expired_rate_limit_buckets(
            db,
            batch_size=batch_size,
            max_batches=max_batches,
        )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="VaxInsight account administration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    admin_parser = subparsers.add_parser("create-admin")
    admin_parser.add_argument("--email", required=True)
    staff_parser = subparsers.add_parser(
        "create-staff",
        help="Provision an active, verified CHW or Health Expert without email delivery",
    )
    staff_parser.add_argument("--email", required=True)
    staff_parser.add_argument("--full-name", default=None)
    staff_parser.add_argument("--role", choices=STAFF_ROLES, required=True)
    cleanup_parser = subparsers.add_parser(
        "cleanup-rate-limits",
        help="Remove a bounded batch of expired rate-limit buckets",
    )
    cleanup_parser.add_argument("--batch-size", type=int, default=None)
    cleanup_parser.add_argument("--max-batches", type=int, default=None)
    args = parser.parse_args()

    if args.command == "cleanup-rate-limits":
        try:
            deleted_count = cleanup_rate_limits(
                batch_size=args.batch_size,
                max_batches=args.max_batches,
            )
        except (RateLimitCleanupError, ValueError) as error:
            parser.exit(1, f"Rate-limit cleanup failed: {error}\n")

        print(f"Expired rate-limit buckets removed: {deleted_count}")
        return

    if args.command == "create-staff":
        password = getpass("Staff password: ")
        confirmation = getpass("Confirm staff password: ")
        if len(password) < 12:
            parser.exit(1, "Staff password must contain at least 12 characters.\n")
        if password != confirmation:
            parser.exit(1, "Staff passwords do not match.\n")

        email = args.email.strip().lower()
        full_name = " ".join(args.full_name.split()) if args.full_name else None
        try:
            create_staff(
                email,
                full_name=full_name,
                role=args.role,
                password=password,
            )
        except ValueError as error:
            parser.exit(1, f"Staff account was not created: {error}\n")

        print(f"Staff account provisioned for {email} ({args.role}).")
        return

    password = getpass("Administrator password: ")
    create_admin(args.email.strip().lower(), password)
    print("Administrator account provisioned.")


if __name__ == "__main__":
    main()
