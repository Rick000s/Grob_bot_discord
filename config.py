import os
from dotenv import load_dotenv

load_dotenv()

# Замініть YOUR_BOT_TOKEN або використовуйте .env файл
TOKEN = os.getenv("DISCORD_TOKEN", "ВАШ_ТОКЕН_ТУТ")

TARGET_USERNAMES = {"_rick_000_", "viktor322"}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': 'True',
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
}

FFmpeg_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}