import os
import requests
import shutil
import subprocess
import threading

CORE_PLUGINS = {
    1: ("ViaVersion.jar", "https://github.com/ViaVersion/ViaVersion/releases/download/5.6.0/ViaVersion-5.6.0.jar"),
    2: ("ViaBackwards.jar", "https://github.com/ViaVersion/ViaBackwards/releases/download/5.6.0/ViaBackwards-5.6.0.jar"),
    3: ("ViaRewind.jar", "https://github.com/ViaVersion/ViaRewind/releases/download/4.0.12/ViaRewind-4.0.12.jar"),
    4: ("Geyser-Spigot.jar", "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot"),
    5: ("floodgate-spigot.jar", "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot"),
    6: ("Chunky.jar", "https://cdn.modrinth.com/data/fALzjamp/versions/P3y2MXnd/Chunky-Bukkit-1.4.40.jar"),
}

MORE_PLUGINS = {
    1: ("ClearLag.jar", "https://cdn.modrinth.com/data/LY9bsstc/versions/aZHtlHAi/ClearLag-1.0.1.jar"),
    2 : ("TAB.jar", "https://cdn.modrinth.com/data/gG7VFbG0/versions/BQc9Xm3K/TAB%20v5.4.0.jar"),
    3 : ("PVDC.jar" , "https://cdn.modrinth.com/data/shwtt0v9/versions/jrKq7Fvp/PVDC-2.3.3.jar")
}


def show_plugin_menu():
    print("\nAvailable Plugins:")
    for idx, (name, _) in MORE_PLUGINS.items():
        print(f" {idx}. {name}")

    print("\nExample input: 1 2 4 6")
    print("Press ENTER to skip plugin installation")


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

    def install_plugins_by_index(self, extra_indexes: list[int] | None = None):
        world_plugins = os.path.join(self.world_dir, "plugins")
        os.makedirs(world_plugins, exist_ok=True)

        def install(jar, url):
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

        for jar, url in CORE_PLUGINS.values():
            install(jar, url)

        if not extra_indexes:
            return

        for idx in extra_indexes:
            if idx not in MORE_PLUGINS:
                print(f"⚠ Invalid extra plugin index: {idx}")
                continue

            jar, url = MORE_PLUGINS[idx]
            install(jar, url)

    def start(self):
        cmd = self.cmd.split()

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


if __name__ == "__main__":

    config = {
        "motd" : "Nikhil Java & Bedrock Server",
        "version": input("MC Version [1.21.8]: ") or "1.21.8",
        "world_name": input("World Name [bedrock]: ") or "bedrock",
        "view-distance": int(input("View Distance [8]: ") or 8),
        "port": 25565,
        "gamemode": "survival",
        "difficulty": "normal",
        "online-mode": False,
        "hardcore": False,
    }

    max_ram = input("Max RAM [2G]: ") or "2G"
    run_cmd = f"java -Xms128M -Xmx{max_ram} -jar server.jar nogui"

    server = MinecraftServer(config, run_cmd)

    server.setup_world()

    # ---- OPTIONAL EXTRA PLUGINS (CORE installs automatically) ----
    show_plugin_menu()
    choice = input("\nSelect extra plugins (optional): ").strip()

    extra_indexes = None
    if choice:
        extra_indexes = [int(x) for x in choice.split() if x.isdigit()]

    server.install_plugins_by_index(extra_indexes)

    server.start()