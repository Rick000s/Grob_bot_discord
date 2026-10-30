import logging
import sys

ICONS = {
    logging.DEBUG: "·",
    logging.INFO: "✅",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "❌",
}


class IconFormatter(logging.Formatter):
    def format(self, record):
        record.icon = ICONS.get(record.levelno, "•")
        return super().format(record)


def setup_logging():
    # Щоб емодзі та кирилиця не ламали консоль Windows
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    formatter = IconFormatter("[%(asctime)s] %(icon)s %(message)s", "%H:%M:%S")

    # Звичайні повідомлення — у stdout (білі в PyCharm), попередження й помилки — у stderr (червоні)
    out = logging.StreamHandler(sys.stdout)
    out.addFilter(lambda record: record.levelno < logging.WARNING)
    out.setFormatter(formatter)

    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.WARNING)
    err.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [out, err]

    # Рядки "ffmpeg process ... terminated" після кожного треку — зайвий шум
    logging.getLogger("discord.player").setLevel(logging.WARNING)
