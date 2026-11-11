from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Build PostgreSQL connection URL safely
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)


# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    hide_parameters=True,
    pool_pre_ping=True,
    connect_args={"sslmode": settings.DB_SSL_MODE},
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
