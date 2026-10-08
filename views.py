import discord
from data_manager import TRACKS_DATA

class TrackSelectView(discord.ui.View):
    def __init__(self, music_player):
        super().__init__(timeout=60)
        self.music_player = music_player

    @discord.ui.select(
        placeholder="Select track",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=track["name"], value=track["url"])
            for track in TRACKS_DATA
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        selected_url = select.values[0]
        track_name = next((t["name"] for t in TRACKS_DATA if t["url"] == selected_url), "Track")

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ You must be in a voice channel!", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        voice_client = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)

        try:
            if voice_client is None:
                voice_client = await channel.connect()
            elif voice_client.channel != channel:
                await voice_client.move_to(channel)

            if guild_id not in self.music_player.queues:
                self.music_player.queues[guild_id] = []

            self.music_player.queues[guild_id].append(selected_url)

            if not voice_client.is_playing():
                self.music_player.play_next(voice_client, guild_id)

            try:
                await interaction.message.delete()
            except:
                pass

            music_ch = self.music_player.get_music_channel(interaction.guild)
            await music_ch.send(
                f"🎧 User **{interaction.user.name}** selected track: **{track_name}** and added it to the queue!")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


class LyricsSelectView(discord.ui.View):
    def __init__(self, music_player):
        super().__init__(timeout=60)
        self.music_player = music_player

    @discord.ui.select(
        placeholder="Choose a song to view lyrics",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=track["name"], value=track["url"])
            for track in TRACKS_DATA
        ]
    )
    async def lyrics_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        selected_url = select.values[0]
        selected_track = next((t for t in TRACKS_DATA if t["url"] == selected_url), None)

        try:
            await interaction.message.delete()
        except:
            pass

        music_ch = self.music_player.get_music_channel(interaction.guild)
        if selected_track:
            await music_ch.send(
                f"📜 **Lyrics for {selected_track['name']}:**\n\n{selected_track.get('lyrics', 'Lyrics not added yet.')}")
        else:
            await interaction.followup.send("❌ Lyrics not found.", ephemeral=True)


class HelpSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Select command description",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="гробовщики", description="Opens the track selection menu for music", emoji="🎧"),
            discord.SelectOption(label="гробовщик / хелп", description="Shows this main command menu", emoji="📖"),
            discord.SelectOption(label="плей / !play", description="Starts or resumes playback", emoji="▶️"),
            discord.SelectOption(label="стоп / !stop", description="Stops music, clears queue and disconnects bot", emoji="⏹️"),
            discord.SelectOption(label="текст", description="Outputs current track lyrics or selection menu", emoji="📜"),
            discord.SelectOption(label="караоке", description="Enables karaoke mode (auto-play and song lyrics)", emoji="🎤"),
            discord.SelectOption(label="стоп караоке", description="Disables karaoke mode", emoji="🛑"),
            discord.SelectOption(label="пропустити / !skip", description="Skips the current track", emoji="⏭️"),
            discord.SelectOption(label="рандом / !random", description="Adds a random track to the queue", emoji="🎲"),
            discord.SelectOption(label="репіт / !repeat", description="Repeats the current track", emoji="🔁"),
        ]
    )
    async def help_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        descriptions = {
            "гробовщики": "🎧 **гробовщики** — opens the track selection menu for music.",
            "гробовщик / хелп": "📖 **гробовщик** — shows the main command menu.",
            "плей / !play": "▶️ **плей** or **!play** — starts or resumes playback.",
            "стоп / !stop": "⏹️ **стоп** or **!stop** — stops music, clears queue and disconnects bot.",
            "текст": "📜 **текст** — outputs current track lyrics or selection menu.",
            "караоке": "🎤 **караоке** — enables karaoke mode (auto-play music, outputs and deletes song lyrics).",
            "стоп караоке": "🛑 **стоп караоке** — disables karaoke mode.",
            "пропустити / !skip": "⏭️ **пропустити** or **!skip** — skips track.",
            "рандом / !random": "🎲 **рандом** or **!random** — adds a random track.",
            "репіт / !repeat": "🔁 **репіт** or **!repeat [count]** — repeats track."
        }

        selected_val = select.values[0]
        desc = descriptions.get(selected_val, "Description missing.")

        await interaction.response.send_message(f"ℹ️ Command info:\n{desc}", ephemeral=True)