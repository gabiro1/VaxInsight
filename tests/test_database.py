from unittest.mock import MagicMock, patch

from app.database.dependencies import get_db


def test_get_db_closes_session():
    mock_session = MagicMock()

    with patch(
        "app.database.dependencies.SessionLocal",
        return_value=mock_session,
    ):
        db_generator = get_db()

        db = next(db_generator)

        assert db is mock_session

        try:
            next(db_generator)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()


def test_get_db_closes_session_after_exception():
    mock_session = MagicMock()

    with patch(
        "app.database.dependencies.SessionLocal",
        return_value=mock_session,
    ):
        db_generator = get_db()

        db = next(db_generator)

        assert db is mock_session

        try:
            db_generator.throw(RuntimeError("Simulated database error"))
        except RuntimeError:
            pass

        mock_session.close.assert_called_once()
