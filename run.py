from nhostapi import MinecraftServer

MORE_PLUGINS = {
    1: ("ClearLag.jar", "https://cdn.modrinth.com/data/LY9bsstc/versions/aZHtlHAi/ClearLag-1.0.1.jar"),
    2: ("TAB.jar", "https://cdn.modrinth.com/data/gG7VFbG0/versions/BQc9Xm3K/TAB%20v5.4.0.jar"),
    3: ("PVDC.jar", "https://cdn.modrinth.com/data/shwtt0v9/versions/jrKq7Fvp/PVDC-2.3.3.jar"),
}


def show_plugin_menu():
    print("\nAvailable Plugins:")
    for idx, (name, _) in MORE_PLUGINS.items():
        print(f" {idx}. {name}")

    print("\nExample input: 1 2")
    print("Press ENTER to skip plugin installation")


# ---------------- CONFIG ----------------

config = {
    "motd": "Nikhil Java & Bedrock Server",
    "version": input("MC Version [1.21.8]: ").strip() or "1.21.8",
    "world_name": input("World Name [bedrock]: ").strip() or "bedrock",
    "view-distance": int(input("View Distance [8]: ").strip() or 8),
    "port": 25565,
    "gamemode": "survival",
    "difficulty": "normal",
    "online-mode": False,
    "hardcore": False,
}

max_ram = input("Max RAM [2G]: ").strip() or "2G"
run_cmd = f"java -Xms128M -Xmx{max_ram} -jar server.jar nogui"

# ---------------- SERVER ----------------

server = MinecraftServer(config, run_cmd)

server.setup_world()

# ---------------- PLUGINS ----------------

show_plugin_menu()
choice = input("\nSelect extra plugins (optional): ").strip()

extra_plugins = None
if choice:
    extra_plugins = [
        MORE_PLUGINS[i]
        for i in map(int, choice.split())
        if i in MORE_PLUGINS
    ]

server.install_plugins(extra_plugins)

# ---------------- START ----------------

server.start()
