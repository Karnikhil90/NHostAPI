#  NHostAPI - GitHub Repository Synchronization and API Tool
#  Copyright (C) 2026 Nikhil Karmakar
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, Final, List, Optional, Tuple

import requests

# --- Configuration (Strongly Typed Constants) ---
REPO_OWNER: Final[str] = "Karnikhil90"
REPO_NAME: Final[str] = "NHostAPI"
BRANCH: Final[str] = "master"

# API Endpoints
TREE_API_URL: Final[str] = (
    f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{BRANCH}?recursive=1"
)
RAW_BASE_URL: Final[str] = (
    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"
)
VERSION_FILE_NAME: Final[str] = "version.txt"

# Local Paths
LOG_DIR: Final[str] = ".logs"
LOG_FILE: Final[str] = os.path.join(LOG_DIR, "update.log")
TIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S"


def _now_iso() -> str:
    """Return current time in ISO-8601 format."""
    return datetime.now().strftime(TIME_FORMAT)


def log_update(message: str) -> None:
    """Log message with ISO timestamp and print to stdout."""
    os.makedirs(LOG_DIR, exist_ok=True)
    line: str = f"[{_now_iso()}] = {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def get_remote_version() -> str:
    """Fetch the version string from GitHub with error handling."""
    url: str = f"{RAW_BASE_URL}/{VERSION_FILE_NAME}"
    response: requests.Response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text.strip()


def get_local_version() -> Optional[str]:
    """Safely read the local version file if it exists."""
    if not os.path.exists(VERSION_FILE_NAME):
        return None
    try:
        with open(VERSION_FILE_NAME, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def download_file(relative_path: str, raw_url: str) -> None:
    """
    Downloads a file using a 'Atomic Write' strategy:
    1. Create directory structure.
    2. Download to a .tmp file.
    3. Rename .tmp to actual filename (prevents corruption on crash).
    """
    temp_path: str = f"{relative_path}.tmp"

    # Ensure directory exists
    dir_name: str = os.path.dirname(relative_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    response: requests.Response = requests.get(raw_url, timeout=15, stream=True)
    response.raise_for_status()

    # Write binary (prevents line-ending issues across Windows/Linux)
    with open(temp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Atomic swap: replace old file with new one
    if os.path.exists(relative_path):
        os.remove(relative_path)
    os.rename(temp_path, relative_path)


def perform_full_update() -> None:
    """Orchestrates the discovery and download of all repo files."""
    log_update("Syncing file structure with GitHub...")

    response: requests.Response = requests.get(TREE_API_URL, timeout=10)
    response.raise_for_status()

    # Parse the Git Tree
    tree: List[dict[str, Any]] = response.json().get("tree", [])

    # Filter for files (blobs) and exclude hidden git files if any
    files_to_update: List[str] = [
        item["path"] for item in tree if item["type"] == "blob"
    ]

    for file_path in files_to_update:
        raw_url: str = f"{RAW_BASE_URL}/{file_path}"
        log_update(f"Synchronizing: {file_path}")
        download_file(file_path, raw_url)


def main() -> None:
    """Main execution block with strict error boundaries."""
    try:
        log_update("Initializing update check...")

        remote_v: str = get_remote_version()
        local_v: Optional[str] = get_local_version()

        if local_v is None:
            log_update("Fresh installation detected. Downloading all files...")
            perform_full_update()
            log_update(f"Successfully installed version {remote_v}")

        elif remote_v != local_v:
            log_update(f"Upgrade available: {local_v} -> {remote_v}")
            perform_full_update()
            log_update("Update completed successfully.")

        else:
            log_update(f"System is up to date (v{local_v}).")

    except requests.RequestException as e:
        log_update(f"Network Level Error: {e}")
        sys.exit(1)
    except Exception as e:
        log_update(f"Critical System Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

    print("=" * 30)
    print("Press any key to close...")

    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.getch()
        else:
            input()
    except Exception:
        pass
