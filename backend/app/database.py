# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

database_url = settings.db_url
connect_args = {}

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif database_url.startswith("postgresql"):
    # Use psycopg3 driver for better SSL support
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Force SSL for Railway PostgreSQL
    if "sslmode" not in database_url:
        database_url = (
            f"{database_url}{'&' if '?' in database_url else '?'}sslmode=require"
        )

engine = create_engine(database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
