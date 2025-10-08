"""Logging setup for the FastAPI WebSocket.

Provides specific configuration for Python's logging module."""
import logging
from pathlib import Path

log_path = Path("/logs")
log_path.mkdir(exist_ok=True)

handler = logging.handlers.TimedRotatingFileHandler(
    filename=Path(log_path / "websocket.log"),
    when="m",
    interval=5,
    backupCount=6
)

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)

logger = logging.getLogger("websocket")
logger.addHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"),