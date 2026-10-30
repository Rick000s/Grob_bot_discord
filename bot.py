import asyncio
import logging
import random

import discord
from discord.ext import commands

from config import TOKEN, TARGET_USERNAMES, IDLE_DISCONNECT_SECONDS
from data_manager import TRACKS_DATA, SPOTIFY_TRACKS
from player import MusicPlayer, find_track, fit_message
from views import TrackSelectView, LyricsSelectView, HelpSelectView
from log_setup import setup_logging

setup_logging()
log = logging.getLogger("grob")

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

player = MusicPlayer(bot)
idle_tasks = {}


@bot.event
async def on_ready():
    log.info(f"Bot {bot.user} is ready to rock queues!")


async def join_author_channel(message):
    """Підключає бота до голосового каналу автора. Повертає None, якщо автор не в голосі."""
    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send("❌ You must be in a voice channel!")
        return None
    return await player.connect(message.author.voice.channel)


@bot.event
async def on_message(message):
    # Ігноруємо ботів і особисті повідомлення (там немає guild)
    if message.author.bot or message.guild is None:
        return

    content_lower = message.content.strip().lower()
    guild = message.guild
    guild_id = guild.id
    music_ch = message.channel

    try:
        if content_lower == "гробовщики":
            await music_ch.send("Select track from menu", view=TrackSelectView(player))

        elif content_lower in ["гробовщик", "хелп", "!help", "хелp"]:
            await music_ch.send("Select command from menu", view=HelpSelectView())

        elif content_lower in ["стоп караоке", "!stopkaraoke"]:
            if guild_id in player.karaoke_channels:
                player.karaoke_channels.discard(guild_id)
                await player.clear_lyrics(guild_id)
                await music_ch.send("🛑 **Karaoke** mode stopped.")
            else:
                await music_ch.send("ℹ️ Karaoke mode was not active.")

        elif content_lower in ["караоке", "!karaoke"]:
            if await join_author_channel(message) is None:
                return
            player.karaoke_channels.add(guild_id)

            if not player.is_busy(guild):
                await music_ch.send(
                    "🎤 **Karaoke** mode enabled! Music started in an infinite loop, song lyrics update in the **karaoke** channel.")
                await player.play_next(guild)
            else:
                await music_ch.send(
                    "🎤 **Karaoke** mode enabled! Lyrics of upcoming tracks will be displayed in the **karaoke** channel.")

        elif content_lower in ["стоп", "!stop"]:
            if await player.reset(guild):
                await music_ch.send("⏹️ Music stopped, queue and karaoke cleared, bot left the channel.")
            else:
                await music_ch.send("❌ Bot is not in a voice channel.")

        elif content_lower in ["плей", "!play"]:
            if await join_author_channel(message) is None:
                return

            if player.is_busy(guild):
                await music_ch.send("ℹ️ Music is already playing.")
                return

            queue = player.queues.setdefault(guild_id, [])
            if not queue:
                last_url = player.current_playing_url.get(guild_id)
                if last_url:
                    queue.append(last_url)
                else:
                    queue.extend(SPOTIFY_TRACKS)

            await music_ch.send("▶️ Playback resumed!")
            await player.play_next(guild)

        elif content_lower in ["текст", "!текст"]:
            curr_url = player.current_playing_url.get(guild_id)
            if curr_url:
                current_track = find_track(curr_url)
                if current_track:
                    await music_ch.send(fit_message(
                        f"📜 **Lyrics of current track ({current_track['name']}):**\n\n"
                        f"{current_track.get('lyrics', 'Lyrics not added yet.')}"))
                else:
                    await music_ch.send("❌ Lyrics for this track not found.")
            else:
                await music_ch.send("📜 Nothing is playing right now. Choose a song from the menu:",
                                    view=LyricsSelectView(player))

        elif content_lower in ["пропустити", "!skip"]:
            voice_client = guild.voice_client
            if voice_client and voice_client.is_playing():
                player.repeat_counts.pop(guild_id, None)
                voice_client.stop()  # after-колбек сам увімкне наступний трек
                await music_ch.send(f"⏭️ User **{message.author.name}** skipped the track!")
            else:
                await music_ch.send("❌ Nothing is playing right now.")

        elif content_lower in ["рандом", "!random"]:
            if await join_author_channel(message) is None:
                return

            random_track = random.choice(TRACKS_DATA)
            player.queues.setdefault(guild_id, []).append(random_track["url"])
            await music_ch.send(
                f"🎲 Random track **{random_track['name']}** added to queue (chosen by **{message.author.name}**)")
            await player.play_next(guild)

        elif content_lower.split(maxsplit=1)[:1] in (["репіт"], ["!repeat"]):
            curr_url = player.current_playing_url.get(guild_id)
            if not curr_url:
                await music_ch.send("❌ Nothing is playing to set repeat!")
                return

            parts = content_lower.split()
            track = find_track(curr_url)
            track_name = track["name"] if track else "Current track"

            if len(parts) > 1 and parts[1].isdigit() and int(parts[1]) > 0:
                count = int(parts[1])
                player.repeat_counts[guild_id] = [curr_url, count - 1]
                await music_ch.send(f"🔁 Track **{track_name}** set to repeat **{count}** times.")
            else:
                player.repeat_counts[guild_id] = [curr_url, -1]
                await music_ch.send(f"🔁 Track **{track_name}** set to **infinite repeat**!")

    except discord.HTTPException as e:
        log.error(f"[{guild.name}] Discord error: {e}")
    except Exception as e:
        log.exception(f"[{guild.name}] Command error: {e!r}")
        try:
            await music_ch.send(f"❌ Error: {e}")
        except discord.HTTPException:
            pass


def humans_in(channel):
    return [m for m in channel.members if not m.bot]


async def leave_if_idle(guild):
    await asyncio.sleep(IDLE_DISCONNECT_SECONDS)
    voice_client = guild.voice_client
    if voice_client and voice_client.channel and not humans_in(voice_client.channel):
        log.info(f"[{guild.name}] Voice channel is empty, leaving.")
        await player.reset(guild)


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    voice_client = guild.voice_client

    # Якщо всі люди вийшли з каналу бота — виходимо через IDLE_DISCONNECT_SECONDS
    if voice_client and voice_client.channel:
        task = idle_tasks.get(guild.id)
        if humans_in(voice_client.channel):
            if task:
                task.cancel()
                idle_tasks.pop(guild.id, None)
        elif not task or task.done():
            idle_tasks[guild.id] = asyncio.create_task(leave_if_idle(guild))

    if member.name in TARGET_USERNAMES and before.channel is None and after.channel is not None:
        try:
            await player.connect(after.channel)
            if player.is_busy(guild):
                return

            queue = player.queues.setdefault(guild.id, [])
            if not queue:
                queue.extend(SPOTIFY_TRACKS)
            log.info(f"User {member.name} joined voice! Starting playlist...")
            await player.play_next(guild)
        except Exception as e:
            log.exception(f"Voice module error: {e!r}")


# log_handler=None — використовуємо наше логування з log_setup.py
bot.run(TOKEN, log_handler=None)
