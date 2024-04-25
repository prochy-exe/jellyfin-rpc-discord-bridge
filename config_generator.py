import os, json, platform, subprocess
supported_platforms = ["Linux", "Windows"]
current_platform = platform.system()
if current_platform not in supported_platforms:
    print("Platform not supported!", current_platform)
    exit(0)
current_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_path, 'config.json')
python_package = "python3" if current_platform == "Linux" else "python"
config_dict = {}

# Covering all the possible arch, aarch variations
def is_arm64():
    return True if "aarch64" in platform.machine().lower() or "armv8" in platform.machine().lower() else False

def is_arm32():
    return True if "aarch" in platform.machine().lower() or "arm" in platform.machine().lower() else False

def is_node_installed():
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
            
def is_git_installed():
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False 

def config():
    if input("Is jellyfin-rpc installed?(y/n)\n") == "y":
        installed_by_installer = input("Did you use jellyfin-rpc installer to install it? (y/n)\n")
        if installed_by_installer == "y":
            if input("Is it installed as a service?(y/n)\n") == "y":
                jellyfin_path = "skip"
            else:
                if current_platform == "Linux":
                    jellyfin_path = os.environ['HOME'] + ".local/bin/jellyfin-rpc"
                else:
                    jellyfin_path = os.environ['APPDATA'] +    os.path.join('jellyfin-rpc', 'jellyfin-rpc.exe')
        else:
            jellyfin_path = rf"{input('Where is your jellyfin rpc located?\n')}"
    else:
        if input("Jellyfin-rpc is required, install now?(y/n)\n") == "y":
            if input("Install automatically?(y/n)\n") == "y":
                subprocess.run(["curl", "-o", os.path.join(current_path, 'installer.py'), "-L", "https://raw.githubusercontent.com/Radiicall/jellyfin-rpc/main/scripts/installer.py"], shell=True)
                if current_platform == "Linux":
                    subprocess.run(["chmod", "+x", 'installer.py'])
                subprocess.run([python_package, os.path.join(current_path, 'installer.py')])
                if current_platform == "Linux":
                    jellyfin_path = os.environ['HOME'] + ".local/bin/jellyfin-rpc"
                else:
                    jellyfin_path = os.environ['APPDATA'] + os.path.join('jellyfin-rpc', 'jellyfin-rpc.exe')
            else:
                print("Manual install requires you to create the config manually, please follow steps here: [https://github.com/Radiicall/jellyfin-rpc/wiki/Installation]")
                print("Downloading latest binary...")
                if current_platform == "Linux":
                    if is_arm32():
                        rpc_binary = "jellyfin-rpc-arm32-linux"
                    elif is_arm64():
                        rpc_binary = "jellyfin-rpc-arm64-linux"
                    else :
                        rpc_binary = "jellyfin-rpc-x86_64-linux"
                else:
                    rpc_binary = "jellyfin-rpc.exe"
                subprocess.run(["curl", "-o", os.path.join(current_path, rpc_binary), "-L", f"https://github.com/Radiicall/jellyfin-rpc/releases/latest/download/{rpc_binary}"], shell=True)
                jellyfin_path = os.path.join(current_path, rpc_binary)
        else:
            print("Config generation can't continue without it, exiting...")
            exit(0)
    config_dict['jellyfin_rpc_path'] = rf"{jellyfin_path}"
    config_dict['node_path'] = os.path.join(current_path, 'arrpc', 'src')
    config_dict['token'] = input("Please input your discord token [https://github.com/prochy-exe/jellyfin-rpc-discord-bridge/wiki/How-do-i-get-the-discord-token%3F]\n")
    print("Choose your RPC style:")
    style1 = "Jellyfin\n"
    style1 += "Anime title\n"
    style1 += "S01 - E01 Episode name\n"
    style1 += "02:03 left\n"
    style2 = "Anime title\n"
    style2 += "S01 - E01 Episode name\n"
    style2 += "Streaming on Jellyfin™\n"
    print(f"------------\n(1)\n{style1}------------\n(2)\n{style2}------------")
    print("So, what's your choice?")
    config_dict['rpc_style'] = int(input()) - 1
    app_title = "Jellyfin" if config_dict['rpc_style'] == 0 else "Anime title"
    print("Choose your RPC type:")
    rpc1 = f"Playing a game\n"
    rpc1 += style1
    rpc2 = f"Watching {app_title}\n" #superior in everyway fr
    rpc2 += style2
    print(f"------------\n(1)\n{rpc1}------------\n(2)\n{rpc2}------------")
    print("So, what's your choice?")
    config_dict['rpc_type'] = int(input()) - 1
    with open(config_path, "w") as file:
            json.dump(config_dict, file, indent=4)
    print("Config generation completed, installing required files now...")
    subprocess.run(["pip", "install", "websocket-client"], shell=True)
    if not is_node_installed:
        if current_platform == "Linux":
            try:
                subprocess.run(["curl", "-sL", "https://deb.nodesource.com/setup_20.x", "|", "sudo", "-E", "bash", "-"], shell=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs"], shell=True)
            except:
                print("Failed installing node.js, please install manually! [https://nodejs.org/en/download]")
        else:
            print("Node.js not found, please install it! [https://nodejs.org/en/download]")
    if not is_git_installed:
        if current_platform == "Linux":
            try:
                subprocess.run(["sudo", "apt-get", "install", "-y", "git"], shell=True)
            except:
                print("Failed installing git, please install manually! [https://git-scm.com/download/linux]")
        else:
            try:
                subprocess.run(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"], shell=True)
            except:
                print("Failed installing git, please install manually! [https://git-scm.com/download/win]")
    print("Cloning arRPC...")
    subprocess.run(["git", "clone", "https://github.com/OpenAsar/arrpc", config_dict['node_path'].removesuffix("src")], shell=True)
    subprocess.run(["npm", "install"], shell=True, cwd=config_dict["node_path"].removesuffix("src"))

if __name__ == "__main__":
    config()