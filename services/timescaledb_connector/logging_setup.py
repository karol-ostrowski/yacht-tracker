"""Logging setup for the custom TimescaleDB connector.
Provides specific configuration for Python's logging module."""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

log_path = Path("/logs")
log_path.mkdir(exist_ok=True)

handler = TimedRotatingFileHandler(
    filename=Path(log_path / "timescaledb_connector.log"),
    when="m",
    interval=5,
    backupCount=6
)

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)

logger = logging.getLogger("tsdb_connector")
logger.addHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"),