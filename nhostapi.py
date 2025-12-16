import os
import requests
import shutil
import subprocess
import threading
import platform
# import tarfile,zipfile 
from packaging.version import Version


# Java - Minecraft mapping (ignore patch versions)
JAVA_MC_MAP = {
    8:  ("1.8.0",  "1.16.5"),
    16: ("1.17.0", "1.17.1"),
    17: ("1.18.0", "1.20.4"),
    21: ("1.20.5", "1.21.9"),
}

JAVA_DOWNLOADS = {
    8: {
        "linux": "https://api.adoptium.net/v3/binary/latest/8/ga/linux/x64/jre/hotspot/normal/eclipse",
        "windows": "https://api.adoptium.net/v3/binary/latest/8/ga/windows/x64/jre/hotspot/normal/eclipse"
    },
    17: {
        "linux": "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jre/hotspot/normal/eclipse",
        "windows": "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jre/hotspot/normal/eclipse"
    },
    21: {
        "linux": "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jre/hotspot/normal/eclipse",
        "windows": "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse"
    }
}

CORE_PLUGINS = {
    1: ("ViaVersion.jar", "https://github.com/ViaVersion/ViaVersion/releases/download/5.6.0/ViaVersion-5.6.0.jar"),
    2: ("ViaBackwards.jar", "https://github.com/ViaVersion/ViaBackwards/releases/download/5.6.0/ViaBackwards-5.6.0.jar"),
    3: ("ViaRewind.jar", "https://github.com/ViaVersion/ViaRewind/releases/download/4.0.12/ViaRewind-4.0.12.jar"),
    4: ("Geyser-Spigot.jar", "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot"),
    5: ("floodgate-spigot.jar", "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot"),
    6: ("Chunky.jar", "https://cdn.modrinth.com/data/fALzjamp/versions/P3y2MXnd/Chunky-Bukkit-1.4.40.jar"),
}


class MinecraftServer:
    def __init__(self, config: dict, cmd: str):
        defaults = {
            "version": "1.21.8",
            "world_name": "world",
            "motd" : "Falback to default",
            "port": 25565,
            "gamemode": "survival",
            "difficulty": "normal",
            "online-mode": False,
            "hardcore": False,
            "view-distance": 8
        }

        self.config = {**defaults, **config}
        self.cmd = cmd

        self.servers_dir = "servers"
        self.versions_dir = "versions"
        self.plugins_dir = "plugins"
        
        self.world_dir = os.path.join(self.servers_dir, self.config["world_name"])

        os.makedirs(self.servers_dir, exist_ok=True)
        os.makedirs(self.versions_dir, exist_ok=True)
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.world_dir, exist_ok=True)

        self.jar_path = None
        self.process = None

    def check_or_download_version(self):
        version = self.config["version"]
        jar_path = os.path.join(self.versions_dir, f"{version}.jar")

        if os.path.exists(jar_path):
            self.jar_path = jar_path
            return jar_path

        print(f"⬇ Downloading Paper {version}")
        api = f"https://api.papermc.io/v2/projects/paper/versions/{version}"
        data = requests.get(api).json()
        build = data["builds"][-1]

        url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{build}/downloads/paper-{version}-{build}.jar"

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(jar_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)

        self.jar_path = jar_path
        return jar_path

    def setup_world(self):
        if not self.jar_path:
            self.check_or_download_version()

        shutil.copy(self.jar_path, os.path.join(self.world_dir, "server.jar"))

        with open(os.path.join(self.world_dir, "eula.txt"), "w") as f:
            f.write("eula=true\n")

        # props = {
        #     # "motd": f"{self.config['world_name']} server",
        #     "difficulty": self.config["difficulty"],
        #     "gamemode": self.config["gamemode"],
        #     "server-port": self.config["port"],
        #     "online-mode": str(self.config["online_mode"]).lower(),
        #     "view-distance": self.config["view-distance"],
        #     "hardcore": str(self.config["hardcore"]).lower(),
        # }
        props = {k: v for k, v in self.config.items() if k != "world_name"}

        self.write_server_properties(props)

    def write_server_properties(self, config: dict):
        """
        Writes server.properties with proper boolean and type handling,
        without using a key map.
        """
        exclude_keys = {"world_name", "version"}

        path = os.path.join(self.world_dir, "server.properties")
        with open(path, "w") as f:
            for k, v in config.items():
                if k in exclude_keys or v is None:
                    continue

                if isinstance(v, bool):
                    v = str(v).lower()
                elif isinstance(v, (int, float)):
                    v = str(v)
                else:
                    v = str(v)

                f.write(f"{k}={v}\n")

    def install_plugins(self, extra_plugins: list[tuple[str, str]] | None = None):
        world_plugins = os.path.join(self.world_dir, "plugins")
        os.makedirs(world_plugins, exist_ok=True)

        def install(jar: str, url: str):
            cache_path = os.path.join(self.plugins_dir, jar)
            world_path = os.path.join(world_plugins, jar)

            if not os.path.exists(cache_path):
                print(f"⬇ Downloading {jar}")
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()
                with open(cache_path, "wb") as f:
                    for c in r.iter_content(8192):
                        if c:
                            f.write(c)

            if not os.path.exists(world_path):
                shutil.copy(cache_path, world_path)
                print(f"✔ Installed {jar}")

        # Always install core plugins
        for jar, url in CORE_PLUGINS.values():
            install(jar, url)

        # Optional extra plugins (tuple-based)
        if not extra_plugins:
            return

        for jar, url in extra_plugins:
            install(jar, url)

    def get_os(self) -> str:
        return "windows" if platform.system().lower().startswith("win") else "linux"

    def ensure_java(self, java_ver: int) -> str:
        os_name = self.get_os()

        base_dir = os.path.join("javas", f"java{java_ver}")
        java_bin = "bin/java.exe" if os_name == "windows" else "bin/java"
        java_path = os.path.join(base_dir, java_bin)

        if os.path.exists(java_path):
            return os.path.abspath(java_path)

        print(f"⬇ Downloading Java {java_ver}")
        os.makedirs(base_dir, exist_ok=True)

        url = JAVA_DOWNLOADS[java_ver][os_name]
        archive = os.path.join(base_dir, "runtime_download")

        r = requests.get(url, stream=True)
        r.raise_for_status()

        with open(archive, "wb") as f:
            for c in r.iter_content(8192):
                if c:
                    f.write(c)

        # extract (ZIP first, then TAR) ----
        extracted = False

        try:
            import zipfile
            with zipfile.ZipFile(archive) as z:
                z.extractall(base_dir)
            extracted = True
        except zipfile.BadZipFile:
            pass

        if not extracted:
            import tarfile
            with tarfile.open(archive) as t:
                t.extractall(base_dir)

        os.remove(archive)

        # ---- flatten Adoptium folder ----
        inner = os.listdir(base_dir)[0]
        inner_path = os.path.join(base_dir, inner)

        for item in os.listdir(inner_path):
            shutil.move(os.path.join(inner_path, item), base_dir)

        os.rmdir(inner_path)

        return os.path.abspath(java_path)

    def replace_java_in_cmd(self, cmd: str, java_bin: str) -> list[str]:
        parts = cmd.split()
        parts[0] = java_bin
        return parts

    def mc_to_java(self, mc_version: str) -> int:
        v = Version(mc_version)
        for java, (start, end) in JAVA_MC_MAP.items():
            if Version(start) <= v <= Version(end):
                return java
        raise RuntimeError(f"No Java mapping for Minecraft {mc_version}")

    def start(self):
        java_ver = self.mc_to_java(self.config["version"])
        java_bin = self.ensure_java(java_ver)

        cmd = self.replace_java_in_cmd(self.cmd, java_bin)

        self.process = subprocess.Popen(
            cmd,
            cwd=self.world_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        def read_output():
            for line in self.process.stdout:
                print(line, end="")

        threading.Thread(target=read_output, daemon=True).start()

        while True:
            try:
                inp = input()
                if self.process.poll() is not None:
                    break

                self.process.stdin.write(inp + "\n")
                self.process.stdin.flush()

                if inp.lower() == "stop":
                    break
            except KeyboardInterrupt:
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
                break
