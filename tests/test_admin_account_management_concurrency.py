import threading
from collections.abc import Callable
from uuid import UUID, uuid4

import pytest
from app.database.database import SessionLocal
from app.models.auth import AuditEvent, RefreshSession
from app.models.user import AccountStatus, User, UserRole
from app.services import auth as auth_service
from app.services.auth import (
    LastActiveAdministratorError,
    change_account_status,
    change_user_role,
)
from sqlalchemy import delete, or_, text
from sqlalchemy.orm import Session

Operation = Callable[[Session], None]
ADMINISTRATOR_LOCK_KEY = 72419031


def _create_users(roles: dict[str, str]) -> dict[str, UUID]:
    db = SessionLocal()
    users = {}

    try:
        for name, role in roles.items():
            user = User(
                id=uuid4(),
                email=f"concurrency-{name}-{uuid4()}@example.com",
                hashed_password="test-hash",
                is_active=True,
                status=AccountStatus.ACTIVE.value,
                role=role,
            )
            db.add(user)
            users[name] = user.id
        db.commit()
        return users
    finally:
        db.close()


def _cleanup_users(user_ids: list[UUID]) -> None:
    db = SessionLocal()
    try:
        db.rollback()
        db.execute(
            delete(AuditEvent).where(
                or_(
                    AuditEvent.actor_user_id.in_(user_ids),
                    AuditEvent.target_user_id.in_(user_ids),
                )
            )
        )
        db.execute(delete(RefreshSession).where(RefreshSession.user_id.in_(user_ids)))
        db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
    finally:
        db.close()


def _read_user_state(user_ids: dict[str, UUID]) -> dict[str, dict[str, object]]:
    db = SessionLocal()
    try:
        users = {name: db.get(User, user_id) for name, user_id in user_ids.items()}
        active_administrators = [
            user
            for user in users.values()
            if user.role == UserRole.ADMINISTRATOR.value
            and user.status == AccountStatus.ACTIVE.value
            and user.is_active is True
        ]
        assert len(active_administrators) == 1
        return {
            name: {
                "role": user.role,
                "status": user.status,
                "is_active": user.is_active,
            }
            for name, user in users.items()
        }
    finally:
        db.close()


def _run_concurrently(
    operations: dict[str, Operation],
    monkeypatch,
) -> dict[str, str | Exception]:
    ready_barrier = threading.Barrier(len(operations))
    first_lock_acquired = threading.Event()
    lock_wait_observed = threading.Event()
    release_first_lock_holder = threading.Event()
    stop_lock_monitor = threading.Event()
    result_lock = threading.Lock()
    results: dict[str, str | Exception] = {}
    acquired_lock = threading.Lock()
    acquired_count = 0
    original_lock = auth_service._lock_administrator_management

    def synchronized_lock(db: Session, target: User) -> None:
        nonlocal acquired_count

        # Both workers reach this barrier before either calls PostgreSQL.
        ready_barrier.wait(timeout=30)
        original_lock(db, target)

        with acquired_lock:
            is_first_holder = acquired_count == 0
            acquired_count += 1

        if is_first_holder:
            first_lock_acquired.set()
            if not lock_wait_observed.wait(timeout=30):
                raise RuntimeError("PostgreSQL advisory-lock wait was not observed")
            if not release_first_lock_holder.wait(timeout=30):
                raise RuntimeError("Timed out releasing the first advisory lock")

    monkeypatch.setattr(
        auth_service,
        "_lock_administrator_management",
        synchronized_lock,
    )

    def monitor_lock_wait() -> None:
        db = SessionLocal()
        try:
            while not stop_lock_monitor.is_set():
                waiting_count = db.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM pg_locks
                        WHERE locktype = 'advisory'
                          AND granted = false
                          AND objid = :lock_key
                        """
                    ),
                    {"lock_key": ADMINISTRATOR_LOCK_KEY},
                )
                db.rollback()
                if waiting_count:
                    lock_wait_observed.set()
                    return
                stop_lock_monitor.wait(0.01)
        finally:
            db.close()

    def worker(name: str, operation: Operation) -> None:
        db = SessionLocal()
        try:
            operation(db)
            outcome: str | Exception = "success"
        except LastActiveAdministratorError:
            db.rollback()
            outcome = "rejected"
        except Exception as error:  # noqa: BLE001 - report worker failures
            db.rollback()
            outcome = error
        finally:
            db.close()

        with result_lock:
            results[name] = outcome

    monitor_thread = threading.Thread(target=monitor_lock_wait, name="lock-monitor")
    threads = [
        threading.Thread(target=worker, args=(name, operation), name=name)
        for name, operation in operations.items()
    ]

    monitor_thread.start()
    for thread in threads:
        thread.start()

    first_lock_was_acquired = first_lock_acquired.wait(timeout=30)
    lock_wait_was_observed = lock_wait_observed.wait(timeout=30)
    release_first_lock_holder.set()

    for thread in threads:
        thread.join(timeout=30)
    stop_lock_monitor.set()
    monitor_thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads), (
        "Concurrent administrator operation did not complete"
    )
    assert not monitor_thread.is_alive(), "Lock monitor did not complete"
    assert first_lock_was_acquired, "The first advisory lock was not acquired"
    assert lock_wait_was_observed, "A PostgreSQL advisory-lock waiter was not observed"
    assert acquired_count == len(operations), "Not every advisory lock was acquired"
    assert set(results) == set(operations)
    assert all(isinstance(outcome, str) for outcome in results.values()), results
    assert sum(outcome == "success" for outcome in results.values()) == 1
    assert sum(outcome == "rejected" for outcome in results.values()) == 1
    return results


def _change_status(actor_id: UUID, target_id: UUID) -> Operation:
    def operation(db: Session) -> None:
        actor = db.get(User, actor_id)
        target = db.get(User, target_id)
        change_account_status(
            db,
            actor=actor,
            target=target,
            new_status=AccountStatus.SUSPENDED.value,
        )

    return operation


def _change_role(actor_id: UUID, target_id: UUID) -> Operation:
    def operation(db: Session) -> None:
        actor = db.get(User, actor_id)
        target = db.get(User, target_id)
        change_user_role(
            db,
            actor=actor,
            target=target,
            role=UserRole.CHW.value,
        )

    return operation


def _assert_admin_removal_results(results: dict[str, str | Exception]) -> None:
    assert all(isinstance(outcome, str) for outcome in results.values()), results
    assert sum(outcome == "success" for outcome in results.values()) == 1
    assert sum(outcome == "rejected" for outcome in results.values()) == 1


@pytest.mark.integration
def test_concurrent_administrators_deactivating_each_other_preserve_one_admin(
    monkeypatch,
):
    user_ids = _create_users(
        {
            "admin_a": UserRole.ADMINISTRATOR.value,
            "admin_b": UserRole.ADMINISTRATOR.value,
            "observer": UserRole.CHW.value,
        }
    )

    try:
        results = _run_concurrently(
            {
                "a_deactivates_b": _change_status(
                    user_ids["admin_a"], user_ids["admin_b"]
                ),
                "b_deactivates_a": _change_status(
                    user_ids["admin_b"], user_ids["admin_a"]
                ),
            },
            monkeypatch,
        )
        _assert_admin_removal_results(results)
        state = _read_user_state(user_ids)

        for operation_name, target_name in (
            ("a_deactivates_b", "admin_b"),
            ("b_deactivates_a", "admin_a"),
        ):
            if results[operation_name] == "success":
                assert state[target_name]["status"] == AccountStatus.SUSPENDED.value
                assert state[target_name]["is_active"] is False
            else:
                assert state[target_name] == {
                    "role": UserRole.ADMINISTRATOR.value,
                    "status": AccountStatus.ACTIVE.value,
                    "is_active": True,
                }
        assert state["observer"] == {
            "role": UserRole.CHW.value,
            "status": AccountStatus.ACTIVE.value,
            "is_active": True,
        }
    finally:
        _cleanup_users(list(user_ids.values()))


@pytest.mark.integration
def test_concurrent_administrators_demoting_each_other_preserve_one_admin(
    monkeypatch,
):
    user_ids = _create_users(
        {
            "admin_a": UserRole.ADMINISTRATOR.value,
            "admin_b": UserRole.ADMINISTRATOR.value,
            "observer": UserRole.CHW.value,
        }
    )

    try:
        results = _run_concurrently(
            {
                "a_demotes_b": _change_role(user_ids["admin_a"], user_ids["admin_b"]),
                "b_demotes_a": _change_role(user_ids["admin_b"], user_ids["admin_a"]),
            },
            monkeypatch,
        )
        _assert_admin_removal_results(results)
        state = _read_user_state(user_ids)

        for operation_name, target_name in (
            ("a_demotes_b", "admin_b"),
            ("b_demotes_a", "admin_a"),
        ):
            if results[operation_name] == "success":
                assert state[target_name]["role"] == UserRole.CHW.value
                assert state[target_name]["status"] == AccountStatus.ACTIVE.value
                assert state[target_name]["is_active"] is True
            else:
                assert state[target_name]["role"] == UserRole.ADMINISTRATOR.value
                assert state[target_name]["status"] == AccountStatus.ACTIVE.value
                assert state[target_name]["is_active"] is True
        assert state["observer"] == {
            "role": UserRole.CHW.value,
            "status": AccountStatus.ACTIVE.value,
            "is_active": True,
        }
    finally:
        _cleanup_users(list(user_ids.values()))


@pytest.mark.integration
def test_mixed_concurrent_administrator_removals_preserve_one_admin(monkeypatch):
    user_ids = _create_users(
        {
            "admin_a": UserRole.ADMINISTRATOR.value,
            "admin_b": UserRole.ADMINISTRATOR.value,
            "observer": UserRole.CHW.value,
        }
    )

    try:
        results = _run_concurrently(
            {
                "a_deactivates_b": _change_status(
                    user_ids["admin_a"], user_ids["admin_b"]
                ),
                "b_demotes_a": _change_role(user_ids["admin_b"], user_ids["admin_a"]),
            },
            monkeypatch,
        )
        _assert_admin_removal_results(results)
        state = _read_user_state(user_ids)

        if results["a_deactivates_b"] == "success":
            assert state["admin_b"]["status"] == AccountStatus.SUSPENDED.value
            assert state["admin_b"]["is_active"] is False
            assert state["admin_a"] == {
                "role": UserRole.ADMINISTRATOR.value,
                "status": AccountStatus.ACTIVE.value,
                "is_active": True,
            }
        else:
            assert state["admin_a"]["role"] == UserRole.CHW.value
            assert state["admin_a"]["status"] == AccountStatus.ACTIVE.value
            assert state["admin_a"]["is_active"] is True
            assert state["admin_b"] == {
                "role": UserRole.ADMINISTRATOR.value,
                "status": AccountStatus.ACTIVE.value,
                "is_active": True,
            }
        assert state["observer"] == {
            "role": UserRole.CHW.value,
            "status": AccountStatus.ACTIVE.value,
            "is_active": True,
        }
    finally:
        _cleanup_users(list(user_ids.values()))
