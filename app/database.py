import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV = ROOT / '.env'
VALUES_ENV = ROOT / 'values' / '.env'
VALUES_EXAMPLE = ROOT / 'values' / '.env.example'

if ROOT_ENV.exists():
    load_dotenv(dotenv_path=ROOT_ENV)
elif VALUES_ENV.exists():
    load_dotenv(dotenv_path=VALUES_ENV)
elif VALUES_EXAMPLE.exists():
    load_dotenv(dotenv_path=VALUES_EXAMPLE)

SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL') or os.getenv('DATABASE_URL')
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "SQLALCHEMY_DATABASE_URL is not set. Please provide SQLALCHEMY_DATABASE_URL in your .env (or values/.env)"
    )

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()