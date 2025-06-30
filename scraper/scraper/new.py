from dotenv import load_dotenv
import os

load_dotenv(override=True) 
PASSWORD = os.getenv("MOODLE_PASSWORD")
print("Password from .env:", PASSWORD)
