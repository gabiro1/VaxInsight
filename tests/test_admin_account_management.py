from uuid import uuid4

import pytest
from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models.auth import AuditEvent, RefreshSession
from app.models.user import AccountStatus, User, UserRole
from app.services.auth import (
    AdministratorSelfModificationError,
    LastActiveAdministratorError,
    change_account_status,
    change_user_role,
)
from sqlalchemy import delete, or_


@pytest.fixture
def admin_test_users():
    """Create isolated PostgreSQL users and clean them up after each test."""

    db = SessionLocal()
    created_ids = []

    def create_user(role, status=AccountStatus.ACTIVE.value):
        user_id = uuid4()

        user = User(
            id=user_id,
            email=f"admin-test-{user_id}@example.com",
            hashed_password=hash_password("StrongPassword123!"),
            is_active=status == AccountStatus.ACTIVE.value,
            status=status,
            role=role,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        created_ids.append(user_id)

        return user

    try:
        yield db, create_user

    finally:
        db.rollback()

        if created_ids:
            db.execute(
                delete(AuditEvent).where(
                    or_(
                        AuditEvent.actor_user_id.in_(created_ids),
                        AuditEvent.target_user_id.in_(created_ids),
                    )
                )
            )

            db.execute(
                delete(RefreshSession).where(RefreshSession.user_id.in_(created_ids))
            )

            db.execute(delete(User).where(User.id.in_(created_ids)))

            db.commit()

        db.close()


@pytest.mark.integration
def test_administrator_cannot_deactivate_own_account(admin_test_users):
    db, create_user = admin_test_users
    admin = create_user(UserRole.ADMINISTRATOR.value)

    with pytest.raises(AdministratorSelfModificationError):
        change_account_status(
            db,
            actor=admin,
            target=admin,
            new_status=AccountStatus.SUSPENDED.value,
        )

    persisted_admin = db.get(User, admin.id)

    assert persisted_admin.status == AccountStatus.ACTIVE.value
    assert persisted_admin.is_active is True


@pytest.mark.integration
def test_administrator_cannot_demote_own_role(admin_test_users):
    db, create_user = admin_test_users
    admin = create_user(UserRole.ADMINISTRATOR.value)

    with pytest.raises(AdministratorSelfModificationError):
        change_user_role(
            db,
            actor=admin,
            target=admin,
            role=UserRole.CHW.value,
        )

    persisted_admin = db.get(User, admin.id)

    assert persisted_admin.role == UserRole.ADMINISTRATOR.value


@pytest.mark.integration
def test_last_active_administrator_cannot_be_deactivated(admin_test_users):
    db, create_user = admin_test_users
    target_admin = create_user(UserRole.ADMINISTRATOR.value)
    actor = create_user(UserRole.CHW.value)

    with pytest.raises(LastActiveAdministratorError):
        change_account_status(
            db,
            actor=actor,
            target=target_admin,
            new_status=AccountStatus.SUSPENDED.value,
        )

    persisted_admin = db.get(User, target_admin.id)

    assert persisted_admin.status == AccountStatus.ACTIVE.value
    assert persisted_admin.is_active is True


@pytest.mark.integration
def test_last_active_administrator_cannot_be_demoted(admin_test_users):
    db, create_user = admin_test_users
    target_admin = create_user(UserRole.ADMINISTRATOR.value)
    actor = create_user(UserRole.CHW.value)

    with pytest.raises(LastActiveAdministratorError):
        change_user_role(
            db,
            actor=actor,
            target=target_admin,
            role=UserRole.REVIEWER.value,
        )

    persisted_admin = db.get(User, target_admin.id)

    assert persisted_admin.role == UserRole.ADMINISTRATOR.value


@pytest.mark.integration
def test_administrator_can_deactivate_another_when_two_exist(admin_test_users):
    db, create_user = admin_test_users
    actor = create_user(UserRole.ADMINISTRATOR.value)
    target = create_user(UserRole.ADMINISTRATOR.value)

    change_account_status(
        db,
        actor=actor,
        target=target,
        new_status=AccountStatus.SUSPENDED.value,
    )

    persisted_actor = db.get(User, actor.id)
    persisted_target = db.get(User, target.id)

    assert persisted_actor.status == AccountStatus.ACTIVE.value
    assert persisted_actor.is_active is True

    assert persisted_target.status == AccountStatus.SUSPENDED.value
    assert persisted_target.is_active is False


@pytest.mark.integration
def test_administrator_can_change_chw_to_reviewer(admin_test_users):
    db, create_user = admin_test_users
    actor = create_user(UserRole.ADMINISTRATOR.value)
    target = create_user(UserRole.CHW.value)

    change_user_role(
        db,
        actor=actor,
        target=target,
        role=UserRole.REVIEWER.value,
    )

    persisted_target = db.get(User, target.id)

    assert persisted_target.role == UserRole.REVIEWER.value
    assert persisted_target.status == AccountStatus.ACTIVE.value
    assert persisted_target.is_active is True
