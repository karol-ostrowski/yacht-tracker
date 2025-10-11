"""Logging module setup for the PyFlink script."""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

log_dir = Path("opt/flink/job_logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / "pyflink_job.log"

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler = TimedRotatingFileHandler(
    filename=log_path,
    when="m",
    interval=5,
    backupCount=6
)

handler.setFormatter(formatter)
logger = logging.getLogger("pyflink_logger")
logger.addHandler(handler)
logger.setLevel(logging.INFO)