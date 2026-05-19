"""
PulseCheck - Health Service Module
Collects system metrics, checks external API reachability, and manages configuration/logging.
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict

import psutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration (Inline Settings)
# ---------------------------------------------------------------------------

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "PulseCheck")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    EXTERNAL_CHECK_URL: str = os.getenv(
        "EXTERNAL_CHECK_URL", "https://www.github.com"
    )
    EXTERNAL_CHECK_TIMEOUT: int = int(os.getenv("EXTERNAL_CHECK_TIMEOUT", "5"))
    EXTERNAL_CHECK_RETRIES: int = int(os.getenv("EXTERNAL_CHECK_RETRIES", "3"))

settings = Settings()

# ---------------------------------------------------------------------------
# Logging (Inline Logger Factory)
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Health Checking Logic
# ---------------------------------------------------------------------------

def _build_retry_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Builds a requests Session with automatic retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_cpu_usage() -> float:
    """Returns current CPU usage as a percentage."""
    try:
        usage = psutil.cpu_percent(interval=0.1)
        logger.debug(f"CPU usage: {usage}%")
        return round(usage, 2)
    except Exception as exc:
        logger.error(f"Failed to retrieve CPU usage: {exc}")
        return -1.0


def get_memory_usage() -> float:
    """Returns current memory usage as a percentage."""
    try:
        usage = psutil.virtual_memory().percent
        logger.debug(f"Memory usage: {usage}%")
        return round(usage, 2)
    except Exception as exc:
        logger.error(f"Failed to retrieve memory usage: {exc}")
        return -1.0


def get_disk_usage() -> float:
    """Returns disk usage percentage for the root partition."""
    try:
        usage = psutil.disk_usage("/").percent
        logger.debug(f"Disk usage: {usage}%")
        return round(usage, 2)
    except Exception as exc:
        logger.error(f"Failed to retrieve disk usage: {exc}")
        return -1.0


def check_external_api() -> str:
    """Checks connectivity to an external API endpoint."""
    url = settings.EXTERNAL_CHECK_URL
    timeout = settings.EXTERNAL_CHECK_TIMEOUT
    retries = settings.EXTERNAL_CHECK_RETRIES

    session = _build_retry_session(retries=retries)

    try:
        logger.info(f"Checking external API connectivity: {url}")
        start = time.monotonic()
        response = session.get(url, timeout=timeout)
        elapsed = round((time.monotonic() - start) * 1000, 2)
        response.raise_for_status()
        logger.info(
            f"External API reachable. Status={response.status_code}, "
            f"Latency={elapsed}ms"
        )
        return "reachable"
    except requests.exceptions.Timeout:
        logger.warning(f"External API timed out after {timeout}s: {url}")
        return "unreachable"
    except requests.exceptions.ConnectionError:
        logger.warning(f"External API connection error: {url}")
        return "unreachable"
    except requests.exceptions.HTTPError as exc:
        logger.warning(f"External API HTTP error: {exc}")
        return "unreachable"
    except Exception as exc:
        logger.error(f"Unexpected error checking external API: {exc}")
        return "unreachable"
    finally:
        session.close()


def build_health_report() -> Dict[str, Any]:
    """Assembles the complete health report payload."""
    logger.info("Building health report...")

    timestamp = datetime.now(timezone.utc).isoformat()
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage()
    external = check_external_api()

    report: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": timestamp,
        "cpu_usage_percent": cpu,
        "memory_usage_percent": memory,
        "disk_usage_percent": disk,
        "external_api_status": external,
    }

    logger.info(
        f"Health report built | cpu={cpu}% memory={memory}% "
        f"disk={disk}% external={external}"
    )
    return report
