from pathlib import Path

from nhostapi import MinecraftServer


def print_banner():
    print(r"""


NNNNNNNN        NNNNNNNNHHHHHHHHH     HHHHHHHHH                                           tttt                        AAA               PPPPPPPPPPPPPPPPP   IIIIIIIIII
N:::::::N       N::::::NH:::::::H     H:::::::H                                        ttt:::t                       A:::A              P::::::::::::::::P  I::::::::I
N::::::::N      N::::::NH:::::::H     H:::::::H                                        t:::::t                      A:::::A             P::::::PPPPPP:::::P I::::::::I
N:::::::::N     N::::::NHH::::::H     H::::::HH                                        t:::::t                     A:::::::A            PP:::::P     P:::::PII::::::II
N::::::::::N    N::::::N  H:::::H     H:::::H     ooooooooooo       ssssssssss   ttttttt:::::ttttttt              A:::::::::A             P::::P     P:::::P  I::::I
N:::::::::::N   N::::::N  H:::::H     H:::::H   oo:::::::::::oo   ss::::::::::s  t:::::::::::::::::t             A:::::A:::::A            P::::P     P:::::P  I::::I
N:::::::N::::N  N::::::N  H::::::HHHHH::::::H  o:::::::::::::::oss:::::::::::::s t:::::::::::::::::t            A:::::A A:::::A           P::::PPPPPP:::::P   I::::I
N::::::N N::::N N::::::N  H:::::::::::::::::H  o:::::ooooo:::::os::::::ssss:::::stttttt:::::::tttttt           A:::::A   A:::::A          P:::::::::::::PP    I::::I
N::::::N  N::::N:::::::N  H:::::::::::::::::H  o::::o     o::::o s:::::s  ssssss       t:::::t                A:::::A     A:::::A         P::::PPPPPPPPP      I::::I
N::::::N   N:::::::::::N  H::::::HHHHH::::::H  o::::o     o::::o   s::::::s            t:::::t               A:::::AAAAAAAAA:::::A        P::::P              I::::I
N::::::N    N::::::::::N  H:::::H     H:::::H  o::::o     o::::o      s::::::s         t:::::t              A:::::::::::::::::::::A       P::::P              I::::I
N::::::N     N:::::::::N  H:::::H     H:::::H  o::::o     o::::ossssss   s:::::s       t:::::t    tttttt   A:::::AAAAAAAAAAAAA:::::A      P::::P              I::::I
N::::::N      N::::::::NHH::::::H     H::::::HHo:::::ooooo:::::os:::::ssss::::::s      t::::::tttt:::::t  A:::::A             A:::::A   PP::::::PP          II::::::II
N::::::N       N:::::::NH:::::::H     H:::::::Ho:::::::::::::::os::::::::::::::s       tt::::::::::::::t A:::::A               A:::::A  P::::::::P          I::::::::I
N::::::N        N::::::NH:::::::H     H:::::::H oo:::::::::::oo  s:::::::::::ss          tt:::::::::::ttA:::::A                 A:::::A P::::::::P          I::::::::I
NNNNNNNN         NNNNNNNHHHHHHHHH     HHHHHHHHH   ooooooooooo     sssssssssss              ttttttttttt AAAAAAA                   AAAAAAAPPPPPPPPPP          IIIIIIIIII


    """)
    print("by Nikhil Karmakar | MIT License")
    print("Pre-Alpha v0.0.2\n")


MORE_PLUGINS = {
    1: (
        "ClearLag.jar",
        "https://cdn.modrinth.com/data/LY9bsstc/versions/aZHtlHAi/ClearLag-1.0.1.jar",
    ),
    2: (
        "TAB.jar",
        "https://cdn.modrinth.com/data/gG7VFbG0/versions/BQc9Xm3K/TAB%20v5.4.0.jar",
    ),
    3: (
        "PVDC.jar",
        "https://cdn.modrinth.com/data/shwtt0v9/versions/jrKq7Fvp/PVDC-2.3.3.jar",
    ),
    4: (
        "voicechat-bukkit-2.6.7.jar",
        "https://hangarcdn.papermc.io/plugins/henkelmax/SimpleVoiceChat/versions/bukkit-2.6.7/PAPER/voicechat-bukkit-2.6.7.jar",
    ),
    5 : ("SkinsRestorer.jar","https://github.com/SkinsRestorer/SkinsRestorer/releases/download/15.9.2/SkinsRestorer.jar")
    }


def show_plugin_menu():
    print("\nAvailable Plugins:")
    for idx, (name, _) in MORE_PLUGINS.items():
        print(f" {idx}. {name}")
    print("\nExample input: 1 2")
    print("Press ENTER to skip plugin installation")


def load_basic_config() -> dict:
    """Load things that are not saved per world."""
    return {
        "motd": input("Enter description (motd) [default]: ").strip()
        or "Nikhil Java & Bedrock Server",
        "view-distance": int(input("View Distance [12]: ").strip() or 12),
    }


def load_saved_config(selected_world: str) -> dict:
    """Load things that are saved for the world or pre-defined."""
    return {
        "world_name": selected_world,
        "version": input("MC Version [1.21.10]: ").strip() or "1.21.10",
        "port": 25565,
        "gamemode": "survival",
        "difficulty": "hard",
        "online-mode": False,
        "hardcore": False,
    }


def choose_world_and_config() -> dict:
    existing_worlds = check_existing_worlds()

    if existing_worlds:
        print("\nExisting Worlds:")
        for i, world in enumerate(existing_worlds, start=1):
            print(f" {i}. {world}")

        choice = input("\nSelect world number (ENTER to create new): ").strip()
        if choice:
            try:
                selected_world = existing_worlds[int(choice) - 1]
            except (ValueError, IndexError):
                print("Invalid choice, creating new world.")
                selected_world = (
                    input("Enter new world name: ").strip() or "my_new_world"
                )
        else:
            selected_world = input("Enter new world name: ").strip() or "my_new_world"
    else:
        print("No existing worlds found.")
        selected_world = input("Enter new world name: ").strip() or "my_new_world"

    # Ask user which type of changes
    print("\nChoose configuration type:")
    print("1. Basic changes (not saved, MOTD, view distance, RAM, etc.)")
    print("2. Saved changes (saved, world name, version, difficulty, etc.)")
    print("3. All changes (basic + saved)")
    config_type = input("Choice [1]: ").strip() or "1"

    basic = load_basic_config()
    saved = load_saved_config(selected_world)

    if config_type == "1":
        saved.update(basic)  # Only apply basic changes
        return saved
    elif config_type == "2":
        return saved  # Only saved changes
    elif config_type == "3":
        saved.update(basic)  # Apply both
        return saved
    else:
        print("Invalid choice, defaulting to Basic changes.")
        saved.update(basic)
        return saved


def check_existing_worlds() -> list[str]:
    worlds = []
    root = Path("servers")

    if not root.exists() or not root.is_dir():
        return worlds

    for item in root.iterdir():
        if item.is_dir() and (item / "server.jar").is_file():
            worlds.append(item.name)

    return worlds


def select_or_create_world(existing_worlds: list[str]) -> str:
    if not existing_worlds:
        print("No existing worlds found.")
        return input("Enter new world name: ").strip() or "my_new_world"

    print("\nExisting Worlds:")
    for i, world in enumerate(existing_worlds, start=1):
        print(f" {i}. {world}")

    choice = input("\nSelect world number (ENTER to create new): ").strip()

    if not choice:
        return input("Enter new world name: ").strip() or "my_new_world"

    try:
        index = int(choice) - 1
        return existing_worlds[index]
    except (ValueError, IndexError):
        print("Invalid choice. Creating new world.")
        return input("Enter new world name: ").strip() or "my_new_world"


def setup_server(config: dict) -> MinecraftServer:
    max_ram = input("Max RAM [2G]: ").strip() or "2G"
    run_cmd = f"java -Xms1M -Xmx{max_ram} -XX:+UseG1GC -jar server.jar nogui --force"

    server = MinecraftServer(config, run_cmd)
    server.setup_world()
    return server


def select_plugins():
    show_plugin_menu()
    choice = input("\nSelect extra plugins (optional): ").strip()

    if not choice:
        return None

    return [MORE_PLUGINS[i] for i in map(int, choice.split()) if i in MORE_PLUGINS]


def main():
    print_banner()

    # First choose world and config type
    config = choose_world_and_config()

    server = setup_server(config)

    plugins = select_plugins()
    server.install_plugins(plugins)

    print("\nStarting Minecraft Server...")
    server.start()


if __name__ == "__main__":
    main()
