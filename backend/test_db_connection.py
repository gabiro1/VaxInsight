from app.database.database import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database connection successful!")
        print("Test query result:", result.scalar())

except SQLAlchemyError as error:
    print("Database connection failed!")
    print("Error:", error)

finally:
    engine.dispose()
