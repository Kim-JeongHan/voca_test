# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Build database URL and connection args
database_url = settings.database_url
connect_args = {}

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif database_url.startswith("postgresql"):
    # Railway PostgreSQL requires SSL
    # Use make_url to properly handle URL with query parameters
    url = make_url(database_url)
    query_dict = dict(url.query)
    if "sslmode" not in query_dict:
        query_dict["sslmode"] = "require"
    url = url.set(query=query_dict)
    database_url = str(url)

engine = create_engine(database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
