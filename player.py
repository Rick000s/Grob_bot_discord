import discord
import yt_dlp
import random
import asyncio
from data_manager import TRACKS_DATA, SPOTIFY_TRACKS
from config import YDL_OPTIONS, FFmpeg_OPTIONS

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.repeat_counts = {}
        self.current_playing_url = {}
        self.karaoke_channels = set()
        self.active_lyrics_messages = {}

    def get_music_channel(self, destination):
        # Якщо передали повідомлення (Message)
        if hasattr(destination, 'channel'):
            return destination.channel
        # Якщо передали канал напряму (TextChannel)
        if hasattr(destination, 'send'):
            return destination
        # Якщо передали сервер (Guild)
        if hasattr(destination, 'text_channels'):
            for channel in destination.text_channels:
                if "🎧" in channel.name:
                    return channel
            return destination.system_channel or destination.text_channels[0]
        return None

    def get_karaoke_channel(self, destination):
        guild = getattr(destination, 'guild', destination)
        if hasattr(guild, 'text_channels'):
            for channel in guild.text_channels:
                if "караоке" in channel.name.lower():
                    return channel
        return self.get_music_channel(destination)

    async def delete_old_message(self, msg):
        try:
            if msg:
                await msg.delete()
        except:
            pass

    def play_next(self, voice_client, guild_id):
        # 1. Видаляємо попередній текст пісні перед переходом
        if guild_id in self.active_lyrics_messages and self.active_lyrics_messages[guild_id]:
            self.bot.loop.create_task(self.delete_old_message(self.active_lyrics_messages[guild_id]))
            self.active_lyrics_messages[guild_id] = None

        # 2. Логіка черги
        if guild_id in self.karaoke_channels:
            if (guild_id not in self.repeat_counts or self.repeat_counts[guild_id][1] == 0):
                if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
                    self.queues[guild_id] = list(SPOTIFY_TRACKS)
                    random.shuffle(self.queues[guild_id])

        if guild_id in self.repeat_counts and self.repeat_counts[guild_id][1] != 0:
            r_url, count = self.repeat_counts[guild_id]
            if count > 0: self.repeat_counts[guild_id][1] -= 1
            actual_url = r_url
        elif guild_id in self.queues and len(self.queues[guild_id]) > 0:
            actual_url = self.queues[guild_id].pop(0)
        else:
            self.current_playing_url[guild_id] = None
            return

        self.current_playing_url[guild_id] = actual_url

        # 3. Надсилаємо новий текст пісні
        if guild_id in self.karaoke_channels:
            karaoke_channel = self.get_karaoke_channel(voice_client.guild)
            track = next((t for t in TRACKS_DATA if t["url"] == actual_url), None)
            if karaoke_channel and track:
                self.bot.loop.create_task(self.send_karaoke_lyrics(karaoke_channel, guild_id, track))

        # 4. Програвання
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(actual_url, download=False)
                if 'entries' in info: info = info['entries'][0]
                url2 = info['url']
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url2, **FFmpeg_OPTIONS))
                voice_client.play(source, after=lambda e: self.play_next(voice_client, guild_id))
            except Exception as e:
                print(f"Error: {e}")
                self.play_next(voice_client, guild_id)

    async def send_karaoke_lyrics(self, channel, guild_id, track):
        try:
            msg = await channel.send(f"🎤 **Зараз у караоке — {track['name']}:**\n\n{track.get('lyrics', 'No lyrics.')}")
            self.active_lyrics_messages[guild_id] = msg
        except:
            pass