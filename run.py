from nhostapi import MinecraftServer

# ---------------- ASCII HEADER ----------------

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

# ---------------- PLUGINS ----------------

MORE_PLUGINS = {
    1: ("ClearLag.jar", "https://cdn.modrinth.com/data/LY9bsstc/versions/aZHtlHAi/ClearLag-1.0.1.jar"),
    2: ("TAB.jar", "https://cdn.modrinth.com/data/gG7VFbG0/versions/BQc9Xm3K/TAB%20v5.4.0.jar"),
    3: ("PVDC.jar", "https://cdn.modrinth.com/data/shwtt0v9/versions/jrKq7Fvp/PVDC-2.3.3.jar"),
    4: ("voicechat-bukkit-2.6.7.jar", "https://hangarcdn.papermc.io/plugins/henkelmax/SimpleVoiceChat/versions/bukkit-2.6.7/PAPER/voicechat-bukkit-2.6.7.jar"),
    5 :("spark-1.10.156-bukkit.jar", "https://ci.lucko.me/job/spark/506/artifact/spark-bukkit/build/libs/spark-1.10.156-bukkit.jar"),
    6 :("playit-minecraft-plugin.jar", "https://github.com/playit-cloud/playit-minecraft-plugin/releases/latest/download/playit-minecraft-plugin.jar")
}

def show_plugin_menu():
    print( "\nAvailable Plugins:")
    for idx, (name, _) in MORE_PLUGINS.items():
        print(f" {idx}. {name}")
    print("\nExample input: 1 2")
    print("Press ENTER to skip plugin installation")

# ---------------- CONFIG ----------------

config = {
    "version": input("MC Version [1.21.8]: ").strip() or "1.21.8",
    "world_name": input("World Name [my_new_world]: ").strip() or "my_new_world",
    "motd": input("Enter description (motd) [Enter for default setting]: ").strip() or "Nikhil Java & Bedrock Server",
    "view-distance": int(input("View Distance [8]: ").strip() or 8),
    "port": 25565,
    "gamemode": "survival",
    "difficulty": "hard",
    "online-mode": False,
    "hardcore": False,
}

max_ram = input("Max RAM [2G]: ").strip() or "2G"
run_cmd = f"java -Xms1M -Xmx{max_ram} -XX:+UseG1GC -jar server.jar nogui --force"

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

print("\nStarting Minecraft Server...")
server.start()
