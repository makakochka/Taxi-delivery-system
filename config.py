import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

SECRET_KEY = os.getenv("SECRET_KEY")
