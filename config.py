import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8615206121:AAF_YysY5PiPfhKTtX5F9AnIr11kNbhIhCU")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5103980244").split(",")))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@Jolawshi_bot_buyirtpa")
DB_PATH = os.getenv("DB_PATH", "jolawshi.db")
