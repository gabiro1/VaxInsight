from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

def build_database_url():
    """Prefer a hosted provider URL and retain DB_* support for local development."""

    if settings.DATABASE_URL:
        database_url = make_url(settings.DATABASE_URL)
        if database_url.drivername == "postgresql":
            database_url = database_url.set(drivername="postgresql+psycopg")
        return database_url

    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
    )


DATABASE_URL = build_database_url()

connect_args = {}
if "sslmode" not in DATABASE_URL.query:
    connect_args["sslmode"] = settings.DB_SSL_MODE


# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    hide_parameters=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)


# Create database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Base class for database models
class Base(DeclarativeBase):
    pass
