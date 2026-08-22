import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("❌ BOT_TOKEN не задан! Добавь его в Environment на Render.")

ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID is None:
    raise ValueError("❌ ADMIN_ID не задан! Добавь его в Environment на Render.")
ADMIN_ID = int(ADMIN_ID)

CHANNEL_ID = os.getenv("CHANNEL_ID")
if CHANNEL_ID is None:
    raise ValueError("❌ CHANNEL_ID не задан! Добавь его в Environment на Render.")
CHANNEL_ID = int(CHANNEL_ID)
