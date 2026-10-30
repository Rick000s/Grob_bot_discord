import os
from dotenv import load_dotenv

load_dotenv()

# Токен береться з .env (DISCORD_TOKEN=...)
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN не знайдено. Створіть файл .env з рядком DISCORD_TOKEN=ваш_токен")

TARGET_USERNAMES = {"_rick_000_", "viktor322"}

# Скільки секунд бот чекає, перш ніж вийти з порожнього голосового каналу
IDLE_DISCONNECT_SECONDS = 60

# Не форсуємо player_client: старий android-клієнт тепер дає SABR-попередження
# і іноді "Requested format is not available". yt-dlp сам обирає робочий клієнт.
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'quiet': True,
    'no_warnings': True,
}

# -reconnect_on_network_error ловить розриви з'єднання (помилка -10054 в лозі).
# Вивід ffmpeg приховано в player.py (stderr=DEVNULL), бо це лише шум від перепідключень.
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 '
                      '-reconnect_on_network_error 1 -reconnect_delay_max 5',
    'options': '-vn'
}
