import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8615206121:AAEpg_mR6nMMijVH5IoIB-Z3EZ7Ob2kSPpA")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5103980244").split(",")))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@Jolawshi_bot_buyirtpa")
DB_PATH = os.getenv("DB_PATH", "jolawshi.db")
