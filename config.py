import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@Jolawshi_bot_buyirtpa")
DB_PATH = os.getenv("DB_PATH", "jolawshi.db")
