# 🎧 Grob Bot Discord

A feature-rich Discord music and karaoke bot written in Python using `discord.py` and `yt-dlp`. It supports interactive menus, queue management, lyrics display, and automatic voice channel joining based on specific user activity.

---

## 🚀 Features

* **Interactive Track Selection:** Choose tracks easily via dropdown menus.
* **Karaoke Mode:** Infinite loop playback with automatic live lyrics updates and message auto-deletion.
* **Queue Management:** Add, skip, stop, or repeat tracks seamlessly.
* **Multi-Server Support:** Fully isolated queues and player states for each Discord server (`guild_id`).
* **Auto-Join Feature:** Automatically joins the voice channel when targeted users connect.
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

### 1. Clone the repository

```bash
git clone https://github.com/Rick000s/Grob_bot_discord.git
cd Grob_bot_discord
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your Discord Bot Token (.env configuration)

Для роботи бота потрібен секретний токен. Оберіть ваш сценарій залежно від наявності файлу:

#### Варіант А: Якщо у вас ВЖЕ є готовий файл `.env`
Просто помістіть його у кореневу папку проєкту `Grob_bot_discord`. Файл має містити такий рядок:
```env
DISCORD_TOKEN=ваш_реальний_токен_бота
```

#### Варіант Б: Якщо у вас НЕМАЄ файлу `.env` (Створюємо з нуля)
Якщо ви налаштовуєте бота вперше, виконайте наступні кроки:

1. **Створіть бота в Discord Developer Portal:**
   * Перейдіть на [Discord Developer Portal](https://discord.com/developers/applications) та авторизуйтеся.
   * Натисніть кнопку **New Application** угорі праворуч та введіть назву вашого бота.
   * У лівому меню перейдіть у вкладку **Bot**.
   * Натисніть **Reset Token** і скопіюйте згенерований токен.

2. **Увімкніть обов'язкові Intents:**
   * На тій самій сторінці вкладки **Bot** прокрутіть вниз до розділу **Privileged Gateway Intents** і активуйте три пункти:
     * `Presence Intent`
     * `Server Members Intent`
     * `Message Content Intent`

3. **Створіть файл `.env`:**
   * У кореневій папці проєкту створіть новий файл і назвіть його точно `.env`.
   * Відкрийте його у PyCharm або будь-якому текстовому редакторі та запишіть туди токен:
     ```env
     DISCORD_TOKEN=ваш_скопійований_токен_сюди
     ```
   * Збережіть файл. Він надійно захищений від публікації за допомогою файлу `.gitignore`.

4. **Запросіть бота на сервер:**
   * Перейдіть у вкладку **OAuth2 -> URL Generator**.
   * У розділі **Scopes** відзначте галочками `bot` та `applications.commands`.
   * У розділі **Bot Permissions** виберіть необхідні права для роботи з голосом і текстом.
   * Скопіюйте згенероване посилання, відкрийте у браузері та додайте бота на свій сервер.

### 4. Run the bot

Запустіть бота через термінал:
```bash
python bot.py
```