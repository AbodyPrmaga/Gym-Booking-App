import os
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve()

class Settings:
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "admin")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "postgres")

st = Settings()
DATABASE_URL = f"postgresql+psycopg2://{st.DB_USER}:{st.DB_PASSWORD}@{st.DB_HOST}:{st.DB_PORT}/{st.DB_NAME}"