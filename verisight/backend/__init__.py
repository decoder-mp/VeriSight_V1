
import os

# Flask secret key
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "db", "verisight.db")
