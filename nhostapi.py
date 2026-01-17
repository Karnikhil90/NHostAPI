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
import platform
import shutil
import subprocess
import threading
import time
import requests
import yaml

from pathlib import Path
from packaging.version import Version
from typing import (
        Any, Dict, Final, List, Optional, 
        Tuple, TypedDict ,Iterable
    )

from utility.NBrouser import NBrouser

# --- Strong Typing for Configuration ---
class ServerConfig(TypedDict, total=False):
    """Defined structure for server configuration to prevent runtime KeyErrors."""

    version: str
    world_name: str
    motd: str
    port: int
    gamemode: str
    difficulty: str
    online_mode: bool
    hardcore: bool
    view_distance: int
    java_address: str
    java_port: int
    auth_type: str
    resource_pack_url: str
    resource_pack_hash: str


# --- Constants & Mappings ---
JAVA_MC_MAP: Final[Dict[int, Tuple[str, str]]] = {
    8: ("1.8.0", "1.12"),
    11: ("1.13", "1.16.5"),
    16: ("1.17", "1.17.1"),
    17: ("1.18", "1.20.4"),
    21: ("1.20.5", "1.21.11"),
}

LATEST_JAVA_LTS: Final[int] = 25

JAVA_DOWNLOADS: Final[Dict[int, Dict[str, str]]] = {
    v: {
        "linux": f"https://api.adoptium.net/v3/binary/latest/{v}/ga/linux/x64/jre/hotspot/normal/eclipse",
        "windows": f"https://api.adoptium.net/v3/binary/latest/{v}/ga/windows/x64/jre/hotspot/normal/eclipse",
    }
    for v in [8, 11, 17, 21, 25]
}

CORE_PLUGINS: Final[Dict[int, Tuple[str, str]]] = {
    1: (
        "ViaVersion.jar",
        "https://github.com/ViaVersion/ViaVersion/releases/download/5.7.0/ViaVersion-5.7.0.jar",
    ),
    2: (
        "ViaBackwards.jar",
        "https://github.com/ViaVersion/ViaBackwards/releases/download/5.7.0/ViaBackwards-5.7.0.jar",
    ),
    3: (
        "ViaRewind.jar",
        "https://github.com/ViaVersion/ViaRewind/releases/download/4.0.12/ViaRewind-4.0.12.jar",
    ),
}

CORE_PLUGINS_PLUS: Final[Dict[int, Tuple[str, str]]] = {
    1: (
        "Geyser-Spigot.jar",
        "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot",
    ),
    2: (
        "floodgate-spigot.jar",
        "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot",
    ),
}


class MinecraftServer:
    def __init__(self, config: ServerConfig, cmd: str) -> None:
        self.defaults: ServerConfig = {
            "version": "1.21.1",
            "world_name": "fall_back_world",
            "motd": "NHostAPI by Nikhil Java & Bedrock Server",
            "port": 25565,
            "gamemode": "survival",
            "difficulty": "normal",
            "online_mode": False,
            "hardcore": False,
            "view_distance": 8,
        }

        self.config: ServerConfig = {**self.defaults, **config}
        self.cmd: str = cmd

        self.servers_dir: Path = Path("servers")
        self.versions_dir: Path = Path("versions")
        self.plugins_cache: Path = Path("plugins")
        self.world_dir: Path = self.servers_dir / str(self.config["world_name"])

        self.browser = NBrouser()

        self._init_directories()

        self.jar_path: Optional[Path] = None
        self.process: Optional[subprocess.Popen] = None

    def _init_directories(self) -> None:
        for p in [
            self.servers_dir,
            self.versions_dir,
            self.plugins_cache,
            self.world_dir,
        ]:
            p.mkdir(parents=True, exist_ok=True)

    def check_or_download_version(self) -> Path:
        """
        Ensure the PaperMC jar for the configured version exists.
        Downloads it if missing, using NBrouser for safe, atomic download.
        """

        version: str = str(self.config.get("version"))
        jar_path: Path = self.versions_dir / f"paper-{version}.jar"

        # Already downloaded
        if jar_path.exists():
            self.jar_path = jar_path
            return jar_path

        # Fetch latest build info
        api_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}"
        try:
            data = requests.get(api_url, timeout=10).json()
            build = data["builds"][-1]
            download_url = f"{api_url}/builds/{build}/downloads/paper-{version}-{build}.jar"
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PaperMC build info: {e}")

        print(f"⬇ Downloading PaperMC {version}...")

        # Ensure versions directory exists
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # Use NBrouser to download with progress and atomic tmp file
        result = self.browser.download(
            url=download_url,
            destination=self.versions_dir,  # NBrouser treats this as directory
            filename=f"paper-{version}.jar",
            show_progress=True,
        )

        self.jar_path = result["path"]
        print(f"✔ PaperMC {version} downloaded to {self.jar_path}")
        return self.jar_path

    def setup_world(self) -> None:
        if not self.jar_path:
            self.check_or_download_version()

        if self.jar_path:
            shutil.copy(self.jar_path, self.world_dir / "server.jar")

        with open(self.world_dir / "eula.txt", "w") as f:
            f.write("eula=true\n")

        props = {
            k: v for k, v in self.config.items() if k not in ["world_name", "version"]
        }
        self.write_server_properties(props)

    def write_server_properties(self, config: Dict[str, Any]) -> None:
        path: Path = self.world_dir / "server.properties"
        with open(path, "w") as f:
            for k, v in config.items():
                if v is None:
                    continue
                val = str(v).lower() if isinstance(v, bool) else str(v)
                f.write(f"{k}={val}\n")

    def setup_geyser(self) -> None:
        geyser_config_path: Path = (
            self.world_dir / "plugins" / "Geyser-Spigot" / "config.yml"
        )
        geyser_config_path.parent.mkdir(parents=True, exist_ok=True)

        if not geyser_config_path.exists():
            with open(geyser_config_path, "w") as f:
                yaml.safe_dump({}, f)

        with open(geyser_config_path, "r") as f:
            config = yaml.safe_load(f) or {}

        config.setdefault("bedrock", {})
        config["bedrock"].update(
            {
                "enabled": True,
                "address": "0.0.0.0",
                "port": 19132,
                "motd1": self.config.get("motd", "GeyserMC Server"),
                "motd2": self.config.get("world_name", "world"),
                "auto-auth": False,
            }
        )

        config.setdefault("remote", {})
        config["remote"].update(
            {
                "address": self.config.get("java_address", "127.0.0.1"),
                "port": self.config.get("java_port", 25565),
                "auth-type": self.config.get("auth_type", "online"),
            }
        )

        config.setdefault("bedrock-resource-pack", {})
        if "resource_pack_url" in self.config:
            config["bedrock-resource-pack"]["url"] = self.config["resource_pack_url"]
            config["bedrock-resource-pack"]["hash"] = self.config.get(
                "resource_pack_hash", ""
            )

        with open(geyser_config_path, "w") as f:
            yaml.safe_dump(config, f, sort_keys=False)

    def ensure_downloaded(
        self,
        browser,
        *,
        download_dir: str | Path,
        files: Iterable[Tuple[str, str]],
        show_progress: bool = True,
    ) -> list[Path]:
        """
        Ensure all files exist inside `download_dir`.

        files: iterable of (filename, url)

        Returns list of resolved Paths.
        """
        download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        resolved: list[Path] = []

        for name, url in files:
            path = download_dir / name

            if not path.exists():
                print(f"⬇ Downloading {name}...")
                result = self.browser.download(
                    url=url,
                    destination=download_dir,
                    filename=name,
                    show_progress=show_progress,
                )
                path = result["path"]

            resolved.append(path)

        return resolved


    def safe_copy(self, src: Path, dst: Path, *, overwrite: bool = False) -> None:
        """
        Copy a file safely with Windows-lock tolerance.
        """
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise FileNotFoundError(src)

        if dst.exists() and not overwrite:
            return

        dst.parent.mkdir(parents=True, exist_ok=True)

        for _ in range(8):
            try:
                shutil.copy(src, dst)
                return
            except PermissionError:
                time.sleep(0.25)

        shutil.copy(src, dst)

    def install_plugins(
        self,
        extra_plugins: Optional[List[Tuple[str, str]]] = None,
        force_plus: bool = False,
    ) -> None:
        world_plugins = self.world_dir / "plugins"
        world_plugins.mkdir(parents=True, exist_ok=True)

        self.plugins_cache.mkdir(parents=True, exist_ok=True)

        core = list(CORE_PLUGINS.values())
        plus = list(CORE_PLUGINS_PLUS.values())

        files = core

        try:
            major_ver = float(str(self.config.get("version", "1.16")).rsplit(".", 1)[0])
            if force_plus or major_ver >= 1.18:
                files += plus
                self.setup_geyser()
        except (ValueError, IndexError):
            pass

        if extra_plugins:
            files += list(extra_plugins)

        cached = self.ensure_downloaded(
            self.browser,
            download_dir=self.plugins_cache,
            files=files,
        )

        for path in cached:
            self.safe_copy(path, world_plugins / path.name)


    def get_os_name(self)->str:
        return (
            "windows" if platform.system().lower().startswith("win") else "linux"
        )
    
    def ensure_java(self, java_ver: int) -> str:
        os_name = self.get_os_name()
        base_dir: Path = Path("javas") / f"java{java_ver}"
        java_bin: str = "bin/java.exe" if os_name == "windows" else "bin/java"
        java_path: Path = base_dir / java_bin

        if java_path.exists():
            return str(java_path.absolute())

        base_dir.mkdir(parents=True, exist_ok=True)
        archive: Path = base_dir / "runtime_dl"

        self.browser.download(JAVA_DOWNLOADS[java_ver][os_name], archive)

        import tarfile
        import zipfile

        try:
            with zipfile.ZipFile(archive) as z:
                z.extractall(base_dir)
        except zipfile.BadZipFile:
            with tarfile.open(archive) as t:
                t.extractall(base_dir)

        archive.unlink()

        inner_folder = next(base_dir.iterdir())
        if inner_folder.is_dir():
            for item in inner_folder.iterdir():
                shutil.move(str(item), str(base_dir))
            inner_folder.rmdir()

        return str(java_path.absolute())

    def mc_to_java(self, mc_version: str) -> int:
        v = Version(mc_version)
        for java, (start, end) in JAVA_MC_MAP.items():
            if Version(start) <= v <= Version(end):
                return java
        highest_end = max(Version(end) for _, (_, end) in JAVA_MC_MAP.items())
        return LATEST_JAVA_LTS if v > highest_end else 17

    def start(self) -> None:
        java_ver: int = self.mc_to_java(str(self.config.get("version")))
        java_bin: str = self.ensure_java(java_ver)

        cmd_parts: List[str] = self.cmd.split()
        cmd_parts[0] = java_bin

        self.process = subprocess.Popen(
            cmd_parts,
            cwd=str(self.world_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def _read_output() -> None:
            if self.process and self.process.stdout:
                for line in self.process.stdout:
                    print(line, end="")

        threading.Thread(target=_read_output, daemon=True).start()

        while self.process and self.process.poll() is None:
            try:
                user_input = input()
                if user_input.lower() == "stop":
                    self.process.stdin.write("stop\n")
                    self.process.stdin.flush()
                    break
                self.process.stdin.write(user_input + "\n")
                self.process.stdin.flush()
            except (KeyboardInterrupt, EOFError):
                if self.process.stdin:
                    self.process.stdin.write("stop\n")
                    self.process.stdin.flush()
                break