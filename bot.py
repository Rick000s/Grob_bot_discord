import discord
from discord.ext import commands
import random

from config import TOKEN, TARGET_USERNAMES
from data_manager import TRACKS_DATA, SPOTIFY_TRACKS
from player import MusicPlayer
from views import TrackSelectView, LyricsSelectView, HelpSelectView

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

player = MusicPlayer(bot)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready to rock queues!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content_lower = message.content.strip().lower()
    guild_id = message.guild.id
    music_ch = player.get_music_channel(message.guild)

    if content_lower == "гробовщики":
        view = TrackSelectView(player)
        music_ch = player.get_music_channel(message)
        await music_ch.send("Select track from menu", view=view)

    elif content_lower in ["гробовщик", "хелп", "!help", "хелp"]:
        view = HelpSelectView()
        await music_ch.send("Select command from menu", view=view)

    elif content_lower in ["стоп караоке", "!stopkaraoke"]:
        if guild_id in player.karaoke_channels:
            player.karaoke_channels.remove(guild_id)
            if guild_id in player.active_lyrics_messages and player.active_lyrics_messages[guild_id]:
                await player.delete_old_message(player.active_lyrics_messages[guild_id])
                player.active_lyrics_messages[guild_id] = None
            await music_ch.send("🛑 **Karaoke** mode stopped.")
        else:
            await music_ch.send("ℹ️ Karaoke mode was not active.")

    elif content_lower in ["караоке", "!karaoke"]:
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("❌ You must be in a voice channel!")
            return

        player.karaoke_channels.add(guild_id)
        channel = message.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)

        try:
            if voice_client is None:
                voice_client = await channel.connect()
            elif voice_client.channel != channel:
                await voice_client.move_to(channel)

            if guild_id not in player.queues:
                player.queues[guild_id] = []

            if not voice_client.is_playing():
                if len(player.queues[guild_id]) == 0:
                    player.queues[guild_id].extend(SPOTIFY_TRACKS)
                player.play_next(voice_client, guild_id)
                await music_ch.send(
                    "🎤 **Karaoke** mode enabled! Music started in an infinite loop, song lyrics update in the **karaoke** channel.")
            else:
                await music_ch.send(
                    "🎤 **Karaoke** mode enabled! Lyrics of upcoming tracks will be displayed in the **karaoke** channel.")
        except Exception as e:
            await music_ch.send(f"❌ Error starting karaoke: {e}")

    elif content_lower in ["стоп", "!stop"]:
        voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)

        if guild_id in player.queues:
            player.queues[guild_id].clear()
        if guild_id in player.repeat_counts:
            del player.repeat_counts[guild_id]
        if guild_id in player.karaoke_channels:
            player.karaoke_channels.remove(guild_id)

        if guild_id in player.active_lyrics_messages and player.active_lyrics_messages[guild_id]:
            await player.delete_old_message(player.active_lyrics_messages[guild_id])
            player.active_lyrics_messages[guild_id] = None

        player.current_playing_url[guild_id] = None

        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            await music_ch.send("⏹️ Music stopped, queue and karaoke cleared, bot left the channel.")
        else:
            await music_ch.send("❌ Bot is not in a voice channel.")

    elif content_lower in ["плей", "!play"]:
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("❌ You must be in a voice channel!")
            return

        channel = message.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)

        try:
            if voice_client is None:
                voice_client = await channel.connect()
            elif voice_client.channel != channel:
                await voice_client.move_to(channel)

            if guild_id not in player.queues:
                player.queues[guild_id] = []

            if len(player.queues[guild_id]) == 0 and not voice_client.is_playing():
                if guild_id in player.current_playing_url and player.current_playing_url[guild_id]:
                    player.queues[guild_id].append(player.current_playing_url[guild_id])
                else:
                    player.queues[guild_id].extend(SPOTIFY_TRACKS)

            if not voice_client.is_playing():
                player.play_next(voice_client, guild_id)
                await music_ch.send("▶️ Playback resumed!")
            else:
                await music_ch.send("ℹ️ Music is already playing.")
        except Exception as e:
            await music_ch.send(f"❌ Error: {e}")

    elif content_lower in ["текст", "!текст"]:
        curr_url = player.current_playing_url.get(guild_id)
        if curr_url:
            current_track = next((t for t in TRACKS_DATA if t["url"] == curr_url), None)
            if current_track:
                await music_ch.send(
                    f"📜 **Lyrics of current track ({current_track['name']}):**\n\n{current_track.get('lyrics', 'Lyrics not added yet.')}")
            else:
                await music_ch.send("❌ Lyrics for this track not found.")
        else:
            view = LyricsSelectView(player)
            await music_ch.send("📜 Nothing is playing right now. Choose a song from the menu:", view=view)

    elif content_lower in ["пропустити", "!skip"]:
        voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_playing():
            if message.guild.id in player.repeat_counts:
                del player.repeat_counts[message.guild.id]
            voice_client.stop()
            await music_ch.send(f"⏭️ User **{message.author.name}** skipped the track!")
        else:
            await music_ch.send("❌ Nothing is playing right now.")

    elif content_lower in ["рандом", "!random"]:
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("❌ You must be in a voice channel!")
            return

        channel = message.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=message.guild)
        random_track = random.choice(TRACKS_DATA)

        try:
            if voice_client is None:
                voice_client = await channel.connect()
            elif voice_client.channel != channel:
                await voice_client.move_to(channel)

            if guild_id not in player.queues:
                player.queues[guild_id] = []

            player.queues[guild_id].append(random_track["url"])

            if not voice_client.is_playing():
                player.play_next(voice_client, guild_id)

            await music_ch.send(
                f"🎲 Random track **{random_track['name']}** added to queue (chosen by **{message.author.name}**)")
        except Exception as e:
            await music_ch.send(f"❌ Error: {e}")

    elif content_lower.startswith("репіт") or content_lower.startswith("!repeat"):
        if guild_id not in player.current_playing_url or not player.current_playing_url[guild_id]:
            await music_ch.send("❌ Nothing is playing to set repeat!")
            return

        parts = message.content.split()
        curr_url = player.current_playing_url[guild_id]
        track_name = next((t["name"] for t in TRACKS_DATA if t["url"] == curr_url), "Current track")

        if len(parts) > 1 and parts[1].isdigit():
            count = int(parts[1])
            player.repeat_counts[guild_id] = [curr_url, count - 1]
            await music_ch.send(f"🔁 Track **{track_name}** set to repeat **{count}** times.")
        else:
            player.repeat_counts[guild_id] = [curr_url, -1]
            await music_ch.send(f"🔁 Track **{track_name}** set to **infinite repeat**!")

    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member, before, after):
    if member.name in TARGET_USERNAMES and before.channel is None and after.channel is not None:
        channel = after.channel
        guild_id = member.guild.id
        voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
        music_ch = player.get_music_channel(member.guild)

        try:
            if voice_client is None:
                voice_client = await channel.connect()
            elif voice_client.channel != channel:
                await voice_client.move_to(channel)

            if guild_id not in player.queues:
                player.queues[guild_id] = []

            if len(player.queues[guild_id]) == 0 and not voice_client.is_playing():
                player.queues[guild_id].extend(SPOTIFY_TRACKS)

            if not voice_client.is_playing():
                print(f"User {member.name} joined voice! Starting playlist...")
                player.play_next(voice_client, guild_id)

        except Exception as e:
            print(f"Voice module error: {e}")


bot.run(TOKEN)