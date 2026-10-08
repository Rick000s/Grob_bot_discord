# 🎧 Grob Bot Discord

A feature-rich Discord music and karaoke bot written in Python using `discord.py` and `yt-dlp`. It supports interactive menus, queue management, lyrics display, and automatic voice channel joining based on specific user activity.

---

## 🚀 Features

* **Interactive Track Selection:** Choose tracks easily via dropdown menus.
* **Karaoke Mode:** Infinite loop playback with automatic live lyrics updates and message auto-deletion.
* **Queue Management:** Add, skip, stop, or repeat tracks seamlessly.
* **Multi-Server Support:** Fully isolated queues and player states for each Discord server (`guild_id`).
* **Auto-Join Feature:** Automatically joins правой войс-канал, когда определенные пользователи заходят в него.
* **Universal Server Compatibility:** Works out of the box on any Discord server without requiring specific channel names.

---

## 📋 Commands & Menus

| Command / Trigger | Description |
| :--- | :--- |
| `гробовщики` | Opens the interactive track selection menu for music. |
| `гробовщик` / `хелп` / `!help` | Shows the main help command menu. |
| `плей` / `!play` | Starts or resumes music playback. |
| `стоп` / `!stop` | Stops music, clears the queue, and disconnects the bot. |
| `текст` / `!текст` | Displays lyrics of the currently playing track or opens a selection menu. |
| `караоке` / `!karaoke` | Enables karaoke mode (infinite loop music + live lyrics). |
| `стоп караоке` / `!stopkaraoke` | Disables karaoke mode. |
| `пропустити` / `!skip` | Skips the current track. |
| `рандом` / `!random` | Adds a random track from the library to the queue. |
| `репіт` / `!repeat [count]` | Repeats the current track (infinitely or a specified number of times). |

---

## 💬 Channel Usage

The bot dynamically responds in the current text channel where commands are issued, making it completely plug-and-play on any server without strict channel name requirements.

---

## 🛠️ Installation & Setup

Follow these steps to run the bot locally:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Rick000s/Grob_bot_discord.git](https://github.com/Rick000s/Grob_bot_discord.git)
   cd Grob_bot_discord