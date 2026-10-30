import asyncio
import logging
import random
import subprocess

import discord
import yt_dlp

from data_manager import TRACKS_DATA, SPOTIFY_TRACKS
from config import YDL_OPTIONS, FFMPEG_OPTIONS

MAX_MESSAGE_LEN = 2000
log = logging.getLogger("grob.player")

# Скільки треків підряд можуть не завантажитись, перш ніж зупинимо відтворення
MAX_FAILED_TRACKS = 5


def find_track(url):
    return next((t for t in TRACKS_DATA if t["url"] == url), None)


def fit_message(text):
    return text if len(text) <= MAX_MESSAGE_LEN else text[:MAX_MESSAGE_LEN - 1] + "…"


class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.repeat_counts = {}
        self.current_playing_url = {}
        self.karaoke_channels = set()
        self.active_lyrics_messages = {}
        self.locks = {}

    def _lock(self, guild_id):
        return self.locks.setdefault(guild_id, asyncio.Lock())

    def is_busy(self, guild):
        # Трек грає або саме завантажується
        vc = guild.voice_client
        playing = vc is not None and (vc.is_playing() or vc.is_paused())
        return playing or self._lock(guild.id).locked()

    def get_music_channel(self, destination):
        # Якщо передали повідомлення (Message) або взаємодію (Interaction)
        if hasattr(destination, 'channel') and destination.channel is not None:
            return destination.channel
        # Якщо передали канал напряму (TextChannel)
        if hasattr(destination, 'send'):
            return destination
        # Якщо передали сервер (Guild) — шукаємо канал, куди бот може писати
        if hasattr(destination, 'text_channels'):
            me = destination.me
            writable = [c for c in destination.text_channels if c.permissions_for(me).send_messages]
            for channel in writable:
                if "🎧" in channel.name:
                    return channel
            system = destination.system_channel
            if system and system.permissions_for(me).send_messages:
                return system
            return writable[0] if writable else None
        return None

    def get_karaoke_channel(self, guild):
        for channel in guild.text_channels:
            if "караоке" in channel.name.lower() and channel.permissions_for(guild.me).send_messages:
                return channel
        return self.get_music_channel(guild)

    async def delete_old_message(self, msg):
        try:
            if msg:
                await msg.delete()
        except discord.HTTPException:
            pass

    async def clear_lyrics(self, guild_id):
        msg = self.active_lyrics_messages.pop(guild_id, None)
        await self.delete_old_message(msg)

    async def connect(self, channel):
        voice_client = channel.guild.voice_client
        if voice_client is None:
            return await channel.connect()
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
        return voice_client

    async def reset(self, guild):
        """Повністю зупиняє музику на сервері та виходить з голосового каналу."""
        guild_id = guild.id
        self.queues.pop(guild_id, None)
        self.repeat_counts.pop(guild_id, None)
        self.karaoke_channels.discard(guild_id)
        self.current_playing_url[guild_id] = None
        await self.clear_lyrics(guild_id)

        voice_client = guild.voice_client
        if voice_client is None:
            return False
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        await voice_client.disconnect(force=True)
        return True

    def _next_url(self, guild_id):
        repeat = self.repeat_counts.get(guild_id)
        if repeat and repeat[1] != 0:
            if repeat[1] > 0:
                repeat[1] -= 1
            return repeat[0]

        queue = self.queues.setdefault(guild_id, [])
        if not queue and guild_id in self.karaoke_channels:
            queue.extend(SPOTIFY_TRACKS)
            random.shuffle(queue)
        return queue.pop(0) if queue else None

    @staticmethod
    def _extract_stream_url(url):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url']

    async def _wait_connected(self, guild, timeout=15):
        # Після обриву (WebSocket 1006) discord.py перепідключається сам — даємо йому час
        for _ in range(timeout):
            voice_client = guild.voice_client
            if voice_client is None:
                return None
            if voice_client.is_connected():
                return voice_client
            await asyncio.sleep(1)
        return None

    async def play_next(self, guild):
        guild_id = guild.id
        async with self._lock(guild_id):
            voice_client = await self._wait_connected(guild)
            if voice_client is None:
                self.current_playing_url[guild_id] = None
                return
            if voice_client.is_playing() or voice_client.is_paused():
                return

            await self.clear_lyrics(guild_id)

            for _ in range(MAX_FAILED_TRACKS):
                url = self._next_url(guild_id)
                if url is None:
                    self.current_playing_url[guild_id] = None
                    return

                try:
                    # yt-dlp блокуючий — запускаємо в окремому потоці, щоб не вішати бота
                    stream_url = await asyncio.to_thread(self._extract_stream_url, url)
                except Exception as e:
                    log.error(f"[{guild.name}] Could not load {url}: {e}")
                    continue

                voice_client = await self._wait_connected(guild)
                if voice_client is None:
                    self.current_playing_url[guild_id] = None
                    return

                try:
                    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
                        stream_url, stderr=subprocess.DEVNULL, **FFMPEG_OPTIONS))
                    voice_client.play(source, after=lambda err: self._after_track(guild, err))
                except discord.ClientException as e:
                    log.error(f"[{guild.name}] Playback error: {e}")
                    self.current_playing_url[guild_id] = None
                    return

                self.current_playing_url[guild_id] = url
                track = find_track(url)
                log.info(f"[{guild.name}] Now playing: {track['name'] if track else url}")
                if guild_id in self.karaoke_channels:
                    await self._send_karaoke_lyrics(guild, url)
                return

            log.error(f"[{guild.name}] {MAX_FAILED_TRACKS} tracks in a row failed, playback stopped.")
            self.current_playing_url[guild_id] = None

    def _after_track(self, guild, error):
        # Викликається з потоку аудіоплеєра, тому планування — тільки через threadsafe
        if error:
            log.error(f"[{guild.name}] Player error: {error}")
        asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop)

    async def _send_karaoke_lyrics(self, guild, url):
        track = find_track(url)
        channel = self.get_karaoke_channel(guild)
        if not track or not channel:
            return
        try:
            msg = await channel.send(fit_message(
                f"🎤 **Зараз у караоке — {track['name']}:**\n\n{track.get('lyrics', 'No lyrics.')}"))
            self.active_lyrics_messages[guild.id] = msg
        except discord.HTTPException as e:
            log.warning(f"[{guild.name}] Could not send lyrics: {e}")
