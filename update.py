from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Optional

import requests

# --- Configuration ---
RAW_CHECK_URL: str = (
    "https://raw.githubusercontent.com/Karnikhil90/NHostAPI/master/version.txt"
)
CURRENT_VERSION_OF_NHOSTAPI: str = "version.txt"
LOG_DIR: str = ".logs"
LOG_FILE: str = os.path.join(LOG_DIR, "update.log")
TIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"


def _now_iso() -> str:
    """Return current time in ISO-8601 format."""
    return datetime.now().strftime(TIME_FORMAT)


def log_update(message: str) -> None:
    """Log message with ISO timestamp and print to user."""
    os.makedirs(LOG_DIR, exist_ok=True)
    line: str = f"[{_now_iso()}] = {message}"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    print(line)


def fetch_remote_content() -> str:
    """Fetch raw file content from GitHub."""
    response = requests.get(RAW_CHECK_URL, timeout=10)
    response.raise_for_status()
    return response.text


def read_local_state() -> Optional[str]:
    """Read locally stored state for comparison."""
    if not os.path.exists(CURRENT_VERSION_OF_NHOSTAPI):
        return None
    with open(CURRENT_VERSION_OF_NHOSTAPI, "r", encoding="utf-8") as f:
        return f.read()


def write_local_state(content: str) -> None:
    """Write new state after successful update."""
    with open(CURRENT_VERSION_OF_NHOSTAPI, "w", encoding="utf-8") as f:
        f.write(content)


def perform_update() -> None:
    """Main update workflow."""
    log_update("Checking for updates")

    remote: str = fetch_remote_content()
    local: Optional[str] = read_local_state()

    if local == remote:
        log_update("No update needed")
        return

    log_update("Update detected")
    write_local_state(remote)
    log_update("Update completed successfully")


def main() -> None:
    """Entry point with hard failure safety."""
    try:
        perform_update()
    except requests.RequestException as e:
        log_update(f"Network error: {e}")
        sys.exit(1)
    except Exception as e:
        log_update(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
