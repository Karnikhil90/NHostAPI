#  NHostAPI - GitHub Repository Synchronization and API Tool
#  Copyright (C) 2026 Nikhil Karmakar
#  GNU GENERAL PUBLIC LICENSE v3

import os
import random
from pathlib import Path
from nhostapi import MinecraftServer

def print_banner():
    print(r"""
 __    __  __    __                         __       ______   _______  ______ 
|  \  |  \|  \  |  \                       |  \     /      \ |       \|      \
| $$\ | $$| $$  | $$  ______    _______  _| $$_   |  $$$$$$\| $$$$$$$\\$$$$$$
| $$$\| $$| $$__| $$ /      \  /       \|   $$ \  | $$__| $$| $$__/ $$ | $$  
| $$$$\ $$| $$    $$|  $$$$$$\|  $$$$$$$ \$$$$$$  | $$    $$| $$    $$ | $$  
| $$\$$ $$| $$$$$$$$| $$  | $$ \$$    \   | $$ __ | $$$$$$$$| $$$$$$$  | $$  
| $$ \$$$$| $$  | $$| $$__/ $$ _\$$$$$$\  | $$|  \| $$  | $$| $$       _| $$_ 
| $$  \$$$| $$  | $$ \$$    $$|        $$   \$$  $$| $$  | $$| $$      |   $$ \
 \$$   \$$ \$$   \$$  \$$$$$$  \$$$$$$$     \$$$$  \$$   \$$ \$$       \$$$$$$
    """)
    print("by Nikhil Karmakar | GNU GENERAL PUBLIC LICENSE v3")
    print("Pre-Alpha v0.0.3\n")

MORE_PLUGINS = {
    1: ("EntityClearer.jar", "https://hangarcdn.papermc.io/plugins/Silverstone/EntityClearer/versions/4.1.3/PAPER/EntityClearer.jar"),
    2: ("TAB.jar", "https://cdn.modrinth.com/data/gG7VFbG0/versions/BQc9Xm3K/TAB%20v5.4.0.jar"),
    3: ("PVDC.jar", "https://cdn.modrinth.com/data/shwtt0v9/versions/jrKq7Fvp/PVDC-2.3.3.jar"),
    4: ("SkinsRestorer.jar", "https://github.com/SkinsRestorer/SkinsRestorer/releases/download/15.9.2/SkinsRestorer.jar"),
    5: ("Plane_ServerAnalytics.jar", "https://github.com/plan-player-analytics/Plan/releases/download/5.6.2965/Plan-5.6-build-2965.jar"),
    6: ("EssentialsX-2.21.2.jar", "https://github.com/EssentialsX/Essentials/releases/download/2.21.2/EssentialsX-2.21.2.jar"),
    7: ("Chunky-Bukkit-1.4.40.jar", "https://cdn.modrinth.com/data/fALzjamp/versions/P3y2MXnd/Chunky-Bukkit-1.4.40.jar"),
    8: ("LagCleanerX-1.2.jar","https://cdn.modrinth.com/data/8XKEf6gK/versions/FxEGkizq/LagCleanerX-1.2.jar")
}

# --- HELPERS ---

def select_from_menu(options: list[str], label: str, default_idx: int = 0) -> str:
    menu_string = " | ".join([f"{i}. {val.capitalize()}" for i, val in enumerate(options, 1)])
    print(f"\nSelect {label}:\n{menu_string}")
    choice = input(f"Choice [{default_idx + 1}]: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(options): return options[idx]
    return options[default_idx]

def get_safe_int(prompt: str, default: int) -> int:
    val = input(f"{prompt} [{default}]: ").strip()
    return int(val) if val.isdigit() else default

# --- CORE LOGIC ---

def check_existing_worlds() -> list[str]:
    root = Path("servers")
    if not root.exists() or not root.is_dir(): return []
    return [item.name for item in root.iterdir() if item.is_dir() and (item / "server.jar").is_file()]

def load_basic_config() -> dict:
    return {
        "motd": input("Enter description (motd) [default]: ").strip() or "NHostAPI by Nikhil || Java & Bedrock Server",
        "view-distance": get_safe_int("View Distance", 12),
    }

def load_saved_config(selected_world: str) -> dict:
    modes = ["survival", "creative", "adventure", "spectator"]
    diffs = ["normal", "easy", "hard", "peaceful"]
    return {
        "world_name": selected_world,
        "version": input("MC Version [1.21.10]: ").strip() or "1.21.10",
        "port": 25565,
        "gamemode": select_from_menu(modes, "Gamemode", 0),
        "difficulty": select_from_menu(diffs, "Difficulty", 2), # Default Hard
        "online-mode": False,
        "hardcore": False,
    }

def get_world_and_action(existing_worlds: list[str]) -> tuple[str, bool]:
    if existing_worlds:
        print("\nExisting Worlds:")
        for i, world in enumerate(existing_worlds, start=1):
            print(f" {i}. {world}")
        
        choice = input("\nSelect world number (ENTER to create new): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(existing_worlds):
            selected = existing_worlds[int(choice) - 1]
            print(f"\nWorld: {selected}\n1. Quick Start | 2. Full Setup/Change Config")
            action = input("Choice [1]: ").strip() or "1"
            return selected, (action == "2")

    new_name = input("Enter new world name [my_new_world]: ").strip() or "my_new_world"
    return new_name, True

def setup_server(config: dict) -> MinecraftServer:
    # Use 2G default for Quick Start, or ask for RAM in Full Setup
    if "version" in config:
        max_ram = input("Max RAM [2G]: ").strip() or "2G"
    else:
        max_ram = "2G"
    
    run_cmd = f"java -Xms1M -Xmx{max_ram} -XX:+UseG1GC -jar server.jar nogui --force"
    return MinecraftServer(config, run_cmd)

def select_plugins():
    print("\nAvailable Extra Plugins:")
    for idx, (name, _) in MORE_PLUGINS.items():
        print(f" {idx}. {name}")
    choice = input("\nSelect extra plugins (e.g., 1 2) or ENTER to skip: ").strip()
    if not choice: return None
    try:
        return [MORE_PLUGINS[int(i)] for i in choice.split() if int(i) in MORE_PLUGINS]
    except ValueError:
        return None

def main():
    print_banner()
    existing_worlds = check_existing_worlds()
    
    # Corrected function call
    selected_world, should_configure = get_world_and_action(existing_worlds)

    if not should_configure:
        # QUICK START PATH
        config = {"world_name": selected_world}
        print(f"\n🚀 Quick Starting: {selected_world}...")
        server = setup_server(config)
        
        # This ensures Core and Core+ plugins are checked/installed automatically
        server.install_plugins() 
    else:
        # FULL CONFIG PATH
        print(f"\n⚙️ Configuring: {selected_world}...")
        
        print("\nChoose configuration type:\n1. Basic | 2. Saved | 3. All")
        c_type = input("Choice [3]: ").strip() or "3"

        config = load_saved_config(selected_world)
        if c_type in ["1", "3"]:
            config.update(load_basic_config())
        
        server = setup_server(config)
        server.setup_world() 
        
        # Install Core + Core+ + User Selected Plugins
        extra_plugins = select_plugins()
        server.install_plugins(extra_plugins)

    print(f"\nStarting Minecraft Server: {selected_world}...")
    server.start()

if __name__ == "__main__":
    main()