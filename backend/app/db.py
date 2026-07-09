import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def get_database_url():
    return (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER','tradfolk')}:"
        f"{os.getenv('POSTGRES_PASSWORD','tradfolk')}@"
        f"{os.getenv('POSTGRES_HOST','db')}:"
        f"{os.getenv('POSTGRES_PORT','5432')}/"
        f"{os.getenv('POSTGRES_DB','tradfolk')}"
    )


engine = create_engine(get_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
