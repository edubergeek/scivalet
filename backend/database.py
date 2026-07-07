import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Get DB_URL from environment or use a default localhost MariaDB URL
# Format: mariadb+mariadbconnector://user:password@host:port/dbname
databaseUrl = os.getenv("DB_URL", "mariadb+mariadbconnector://scivalet_user:scivalet_pass@localhost:3306/scivalet")

# Create SQLAlchemy engine with connection pool settings
dbEngine = create_engine(
    databaseUrl,
    pool_recycle=3600,
    pool_pre_ping=True
)

# Create a sessionmaker configured to use our dbEngine
sessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=dbEngine
)

# Define declarative base for model classes
databaseBase = declarative_base()

def getDatabase():
    """
    Dependency generator for obtaining database sessions in FastAPI routes
    and ensuring the session is closed after execution.
    """
    dbSession = sessionLocal()
    try:
        yield dbSession
    finally:
        dbSession.close()
