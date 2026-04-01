"""
Configures application logging.

Logs are written to:
  logs/app.log          — all levels (DEBUG+), rotated at 10 MB, 5 backups kept

Uvicorn's access/error loggers are captured into the same file so every
POST /jobs/1/score and its traceback appear in one place.
"""
import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"
MAX_BYTES = 10 * 1024 * 1024   # 10 MB per file
BACKUP_COUNT = 5                # keep app.log + app.log.1 … app.log.5

LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    console_handler.setLevel(logging.INFO)

    # Root logger — catches app loggers
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Capture uvicorn's own loggers into the same file
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
