import os
import subprocess
import sys
import shutil
import socket
import time
import re

# --- CONFIGURATION ---
MODEL_EXTENSION = ".gguf"
SKIP_DIRS = {'/proc', '/sys', '/dev', '/run', '/tmp', '/var/lib/docker', '/var/lib/containers'}
EXTERNAL_DRIVE_PATHS = ['/media', '/mnt', '/run/media']
VERSION = "13.0 - Diagnostic Edition"
HAS_SUDO = False

# --- UI & COLORS ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    os.system('clear')

def print_header(title):
    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD} {title}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.ENDC}")

# --- SYSTEM UTILITIES ---
def is_installed(tool):
    """Bulletproof check for installed binaries. Bypasses stale PATH environments."""
    if shutil.which(tool):
        return True
    common_paths = [
        f"/usr/local/bin/{tool}", f"/usr/bin/{tool}", f"/bin/{tool}", 
        f"/opt/bin/{tool}", os.path.expanduser(f"~/.local/bin/{tool}")
    ]
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    return False

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_system_stats():
    stats = {"ram": "Unknown", "disk": "Unknown"}
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            available_kb = [int(line.split()[1]) for line in lines if "MemAvailable" in line][0]
            stats["ram"] = f"{available_kb / (1024**2):.1f} GB"
        total, used, free = shutil.disk_usage("/")
        stats["disk"] = f"{free / (1024**3):.1f} GB Free"
    except Exception:
        pass
    return stats

def manage_firewall(action="open", port="11434"):
    # FIX: Removed duplicate "allow" in the delete command
    if HAS_SUDO and is_installed("ufw"):
        if action == "open":
            cmd = ["sudo", "ufw", "allow", f"{port}/tcp"]
        else:
            cmd = ["sudo", "ufw", "delete", "allow", f"{port}/tcp"]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            pass

# --- DEPENDENCY MANAGEMENT ---
def check_sudo_access():
    global HAS_SUDO
    try:
        subprocess.run(["sudo", "-n", "true"], check=True, capture_output=True)
        HAS_SUDO = True
    except subprocess.CalledProcessError:
        HAS_SUDO = False

def pre_flight_check():
    print_header("🛫 Running Pre-Flight Checks")
    check_sudo_access()
    
    if not is_installed("curl"):
        print(f"{Colors.FAIL}❌ 'curl' is missing. Please install it manually (e.g., sudo apt install curl) and restart.{Colors.ENDC}")
        sys.exit(1)

    if not is_installed("ollama"):
        print(f"\n{Colors.WARNING}⚠️ Ollama is not installed. This is required for core functionality.{Colors.ENDC}")
        if input("Install Ollama now? (y/N): ").strip().lower() == 'y':
            print(f"{Colors.BLUE}Note: The installer may ask for your sudo password.{Colors.ENDC}")
            try:
                subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
                time.sleep(1) 
            except subprocess.CalledProcessError:
                print(f"\n{Colors.FAIL}❌ The Ollama installation script failed.{Colors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.FAIL}🛑 Installation aborted by user.{Colors.ENDC}")

    if not is_installed("docker"):
        print(f"\n{Colors.WARNING}⚠️ Docker is not installed (Required for Open WebUI).{Colors.ENDC}")
        if input("Install Docker now? (y/N): ").strip().lower() == 'y':
            print(f"{Colors.BLUE}Note: The installer may ask for your sudo password.{Colors.ENDC}")
            try:
                subprocess.run("curl -fsSL https://get.docker.com | sh", shell=True, check=True)
                time.sleep(1)
            except subprocess.CalledProcessError:
                print(f"\n{Colors.FAIL}❌ The Docker installation script failed.{Colors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.FAIL}🛑 Docker installation aborted.{Colors.ENDC}")

    if not is_installed("cloudflared"):
        print(f"\n{Colors.WARNING}⚠️ Cloudflared is not installed (Required for WAN Tunnels).{Colors.ENDC}")
        if input("Install Cloudflared now? (y/N): ").strip().lower() == 'y':
            try:
                subprocess.run("curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb", shell=True, check=True)
                subprocess.run(["sudo", "dpkg", "-i", "/tmp/cloudflared.deb"], check=True)
                time.sleep(1)
            except subprocess.CalledProcessError:
                print(f"\n{Colors.FAIL}❌ Cloudflared installation failed.{Colors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.FAIL}🛑 Cloudflared installation aborted.{Colors.ENDC}")

    print_header("📊 Dependency Status Report")
    
    def status(cmd):
        return f"{Colors.GREEN}✅ Installed{Colors.ENDC}" if is_installed(cmd) else f"{Colors.FAIL}❌ Missing{Colors.ENDC}"
        
    print(f" {Colors.BOLD}• Curl:{Colors.ENDC}         {status('curl')}")
    print(f" {Colors.BOLD}• Ollama:{Colors.ENDC}       {status('ollama')}")
    print(f" {Colors.BOLD}• Docker:{Colors.ENDC}       {status('docker')}")
    print(f" {Colors.BOLD}• Cloudflared:{Colors.ENDC}  {status('cloudflared')}")
    print("\n" + "="*60)
    
    if not is_installed("ollama"):
        print(f"{Colors.FAIL}⚠️ WARNING: Ollama is missing. Most features will fail to launch.{Colors.ENDC}")
        
    input(f"{Colors.CYAN}{Colors.BOLD}Press [Enter] to proceed to the Dashboard...{Colors.ENDC}")

# --- CORE FUNCTIONS ---
def configure_ollama_network(host="0.0.0.0"):
    print(f"\n{Colors.BLUE}🌐 Routing Ollama backend to {host}...{Colors.ENDC}")
    
    if HAS_SUDO or is_installed("sudo"):
        override_dir = "/etc/systemd/system/ollama.service.d"
        override_file = os.path.join(override_dir, "override.conf")
        service_config = f"[Service]\nEnvironment=\"OLLAMA_HOST={host}\"\n"
        try:
            subprocess.run(["sudo", "mkdir", "-p", override_dir], check=True)
            # FIX: Use sudo tee to write directly instead of /tmp race condition
            proc = subprocess.run(
                ["sudo", "tee", override_file],
                input=service_config,
                capture_output=True,
                text=True,
                check=True
            )
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "ollama"], check=True)
            
            if host == "0.0.0.0": manage_firewall("open", "11434")
            return True
        except subprocess.CalledProcessError:
            print(f"{Colors.WARNING}⚠️ Systemd configuration failed. Falling back to local mode.{Colors.ENDC}")
    
    print(f"{Colors.WARNING}⚠️ Starting lightweight local server instance...{Colors.ENDC}")
    try:
        subprocess.run(["pkill", "ollama"], capture_output=True)
        env = os.environ.copy()
        env["OLLAMA_HOST"] = host
        subprocess.Popen(["ollama", "serve"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2) 
        return True
    except Exception as e:
        print(f"{Colors.FAIL}❌ Failed to start local server: {e}{Colors.ENDC}")
        return False

def start_open_webui():
    print_header("🖥️  Starting Open WebUI (Docker Bridge)")
    
    if not is_installed("docker"):
        print(f"{Colors.FAIL}❌ Docker is not installed on this system.{Colors.ENDC}")
        return

    docker_cmd_base = ["sudo", "docker"] if (HAS_SUDO or is_installed("sudo")) else ["docker"]

    try:
        check_cmd = subprocess.run(docker_cmd_base + ["ps", "-a", "-q", "-f", "name=open-webui"], capture_output=True, text=True)
        
        if check_cmd.stdout.strip():
            print(f"{Colors.BLUE}▶️  Starting existing Open WebUI container...{Colors.ENDC}")
            subprocess.run(docker_cmd_base + ["start", "open-webui"], check=True)
        else:
            print(f"{Colors.BLUE}⬇️  Downloading Open WebUI (This will take a few minutes)...{Colors.ENDC}")
            cmd = docker_cmd_base + [
                "run", "-d", 
                "-p", "3000:8080", 
                "--add-host=host.docker.internal:host-gateway",
                "-e", "OLLAMA_BASE_URL=http://host.docker.internal:11434",
                "-e", "HF_ENDPOINT=https://hf-mirror.com",
                "-e", "HF_TOKEN=hf_your_actual_token_here",
                "-v", "open-webui:/app/backend/data",
                "--name", "open-webui",
                "--restart", "always",
                "ghcr.io/open-webui/open-webui:main"
            ]
            subprocess.run(cmd, check=True)
        
        # Diagnostics Engine: Verify the container actually survived startup
        # FIX: Increased wait from 5s to 15s — Open WebUI takes time to initialize
        print(f"\n{Colors.BLUE}⏳ Verifying container stability (waiting 15 seconds)...{Colors.ENDC}")
        time.sleep(15)
        
        status_cmd = subprocess.run(docker_cmd_base + ["inspect", "-f", "{{.State.Running}}", "open-webui"], capture_output=True, text=True)
        
        if status_cmd.stdout.strip() != "true":
            print(f"\n{Colors.FAIL}❌ FATAL: The Open WebUI container crashed immediately after starting.{Colors.ENDC}")
            print(f"{Colors.WARNING}This is usually caused by Out-Of-Memory (OOM) on low-RAM hardware, or corrupted Docker volumes.{Colors.ENDC}")
            print(f"\n{Colors.BOLD}--- CRASH LOGS (Last 15 lines) ---{Colors.ENDC}")
            logs_cmd = subprocess.run(docker_cmd_base + ["logs", "--tail", "15", "open-webui"], capture_output=True, text=True)
            print(f"{Colors.FAIL}{logs_cmd.stderr or logs_cmd.stdout}{Colors.ENDC}")
            print("----------------------------------\n")
            
            print(f"{Colors.CYAN}If this is an OOM error, you may need to stop the Ollama model first, or add a swap file to your system.{Colors.ENDC}")
            return
            
        manage_firewall("open", "3000")
        lan_ip = get_lan_ip()
        
        print(f"\n{Colors.GREEN}✅ Docker Container is running and stable!{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}Access the dashboard locally at: http://{lan_ip}:3000{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  CRITICAL: The Open WebUI backend takes 1 to 3 minutes to initialize.")
        print(f"   If the site 'Cannot be reached', wait 60 seconds and refresh the browser.{Colors.ENDC}")
        
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}❌ Docker execution failed. Ensure your user is in the 'docker' group if running without sudo.{Colors.ENDC}")

def launch_cloudflare_tunnel():
    print_header("☁️  Cloudflare WAN Tunnel")
    if not is_installed("cloudflared"):
        print(f"{Colors.FAIL}❌ Cloudflare Tunnels (cloudflared) is not installed.{Colors.ENDC}")
        return

    print("What do you want to expose to the internet?")
    print(f"[{Colors.CYAN}1{Colors.ENDC}] The raw Ollama API (Port 11434)")
    print(f"[{Colors.CYAN}2{Colors.ENDC}] The Open WebUI Interface (Port 3000)")
    
    choice = input(f"\nSelect port to tunnel [{Colors.CYAN}1-2{Colors.ENDC}]: ").strip()

    # FIX: Explicit validation instead of silent default
    if choice == '1':
        port = "11434"
    elif choice == '2':
        port = "3000"
    else:
        print(f"{Colors.WARNING}⚠️ Invalid choice. Please enter 1 or 2.{Colors.ENDC}")
        return
    
    if choice == '1':
        print(f"{Colors.WARNING}🔒 Locking Ollama to localhost for secure API tunneling...{Colors.ENDC}")
        configure_ollama_network("127.0.0.1")
        
    print(f"\n{Colors.GREEN}🚀 Starting tunnel on port {port}...{Colors.ENDC}")
    print(f"{Colors.WARNING}Press Ctrl+C to close the tunnel.{Colors.ENDC}\n")
    print(f"{Colors.BLUE}⏳ Waiting for tunnel URL...{Colors.ENDC}\n")

    # FIX: Read cloudflared stderr line by line, extract and display ONLY the trycloudflare.com URL
    url_pattern = re.compile(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com')
    tunnel_url = None

    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stderr:
            match = url_pattern.search(line)
            if match and not tunnel_url:
                tunnel_url = match.group(0)
                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print(f"{Colors.GREEN}{Colors.BOLD}  ✅ Tunnel is LIVE!{Colors.ENDC}")
                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print(f"\n  🌐 Public URL: {Colors.CYAN}{Colors.UNDERLINE}{tunnel_url}{Colors.ENDC}\n")
                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print(f"{Colors.WARNING}  Press Ctrl+C to close the tunnel.{Colors.ENDC}\n")

        process.wait()

    except KeyboardInterrupt:
        if process:
            process.terminate()
        print(f"\n\n{Colors.GREEN}✅ Tunnel closed safely.{Colors.ENDC}")

def stop_services():
    print(f"\n{Colors.WARNING}🛑 Stopping services...{Colors.ENDC}")
    try:
        if HAS_SUDO or is_installed("sudo"):
            subprocess.run(["sudo", "systemctl", "stop", "ollama"], capture_output=True)
        subprocess.run(["pkill", "ollama"], capture_output=True) 
        
        if is_installed("docker"):
            docker_cmd_base = ["sudo", "docker"] if (HAS_SUDO or is_installed("sudo")) else ["docker"]
            subprocess.run(docker_cmd_base + ["stop", "open-webui"], capture_output=True)
            
        print(f"{Colors.GREEN}✅ Services stopped successfully.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error during shutdown: {e}{Colors.ENDC}")

def find_gguf_models(start_paths):
    models = []
    for base_path in start_paths:
        if not os.path.exists(base_path): continue
        for root, dirs, files in os.walk(base_path):
            if any(root.startswith(skip) for skip in SKIP_DIRS):
                dirs[:] = []
                continue
            try:
                for file in files:
                    if file.endswith(MODEL_EXTENSION):
                        models.append(os.path.join(root, file))
            except PermissionError: continue
    return models

def setup_and_run_ollama():
    print_header("🔍 GGUF Model Scanner")
    search_paths = []
    if input(f"Scan external drives (USB/HDD)? (y/N): ").strip().lower() == 'y': 
        search_paths.extend(EXTERNAL_DRIVE_PATHS)

    search_root = os.path.expanduser("~") 
    scan_choice = input(f"Press [Enter] to scan Home or type 'root' to scan entire system (/): ").strip().lower()
    search_paths.append("/" if scan_choice == 'root' else search_root)

    print(f"\n{Colors.BLUE}Searching...{Colors.ENDC}")
    models = find_gguf_models(search_paths)
    
    if not models:
        print(f"{Colors.FAIL}❌ No models found.{Colors.ENDC}")
        return
        
    print(f"\n{Colors.BOLD}--- Found Models ---{Colors.ENDC}")
    for i, m in enumerate(models): print(f"[{Colors.CYAN}{i+1}{Colors.ENDC}] {m}")
        
    try:
        choice = input(f"\nSelect a model [{Colors.CYAN}1-{len(models)}{Colors.ENDC}] or 'q' to cancel: ").strip().lower()
        if choice == 'q': return
        target_model = models[int(choice) - 1]
    except (ValueError, IndexError):
        print(f"{Colors.WARNING}⚠️ Invalid selection.{Colors.ENDC}")
        return

    default_name = f"{os.path.splitext(os.path.basename(target_model))[0].lower()}:community"
    name_input = input(f"\nCustom name for Ollama registry (default: {default_name}): ").strip()
    model_name = name_input if name_input else default_name

    modelfile_path = os.path.join(os.path.dirname(target_model), "Modelfile_temp")
    try:
        with open(modelfile_path, 'w') as f:
            f.write(f"FROM \"{target_model}\"\nPARAMETER temperature 0.7\nSYSTEM \"You are a helpful AI assistant.\"\n")
        print(f"\n{Colors.BLUE}📦 Building '{model_name}' in Ollama. Please wait...{Colors.ENDC}")
        subprocess.run(["ollama", "create", model_name, "-f", modelfile_path], capture_output=True, text=True)
        print(f"{Colors.GREEN}✅ Built successfully! Model is ready for inference.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}", file=sys.stderr)
    finally:
        if os.path.exists(modelfile_path): os.remove(modelfile_path)

def manage_installed_models():
    print_header("📦 Installed Ollama Models")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        print(result.stdout)
        
        del_choice = input(f"\n{Colors.WARNING}Type a model name to DELETE it, or press Enter to return:{Colors.ENDC} ").strip()
        # FIX: Validate model name input — only allow safe characters
        if del_choice:
            if not re.match(r'^[a-zA-Z0-9_\-\.:]+$', del_choice):
                print(f"{Colors.FAIL}❌ Invalid model name. Only letters, numbers, hyphens, underscores, dots, and colons are allowed.{Colors.ENDC}")
                return
            subprocess.run(["ollama", "rm", del_choice])
            print(f"{Colors.GREEN}✅ Model '{del_choice}' deleted.{Colors.ENDC}")
            
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}❌ Could not fetch models. Is Ollama running?{Colors.ENDC}")

def main_menu():
    pre_flight_check()
    check_sudo_access() # Refresh status
    
    while True:
        stats = get_system_stats()
        clear_screen()
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*65}{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD} 🧠 GGUF Manager & Deployment Dashboard (v{VERSION}){Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*65}{Colors.ENDC}")
        
        perm_status = f"{Colors.GREEN}ROOT CAPABLE{Colors.ENDC}" if HAS_SUDO else f"{Colors.WARNING}STANDARD USER{Colors.ENDC}"
        print(f" {Colors.BOLD}🖥️  Target IP:{Colors.ENDC} {Colors.GREEN}{get_lan_ip()}{Colors.ENDC} | {Colors.BOLD}Mode:{Colors.ENDC} {perm_status}")
        print(f" {Colors.BOLD}💾 System:{Colors.ENDC}    {Colors.WARNING}RAM: {stats['ram']} | Disk: {stats['disk']}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*65}{Colors.ENDC}\n")
        
        print(f"[{Colors.CYAN}1{Colors.ENDC}] 📦 Scan & Build a .gguf Model")
        print(f"[{Colors.CYAN}2{Colors.ENDC}] 📋 Manage Installed Models")
        print(f"[{Colors.CYAN}3{Colors.ENDC}] 🚀 Start Backend API (Port 11434)")
        print(f"[{Colors.CYAN}4{Colors.ENDC}] 🌐 Start Open WebUI Dashboard (Port 3000)")
        print(f"[{Colors.CYAN}5{Colors.ENDC}] ☁️  Launch WAN Tunnel (Cloudflare)")
        print(f"[{Colors.CYAN}6{Colors.ENDC}] 🛑 Stop All Services")
        print(f"[{Colors.FAIL}7{Colors.ENDC}] ❌ Exit")
        
        choice = input(f"\nSelect an action [{Colors.CYAN}1-7{Colors.ENDC}]: ").strip()
        
        if choice == '1':
            setup_and_run_ollama()
            input(f"\n{Colors.BOLD}Press Enter to return...{Colors.ENDC}")
        elif choice == '2':
            manage_installed_models()
            input(f"\n{Colors.BOLD}Press Enter to return...{Colors.ENDC}")
        elif choice == '3':
            if configure_ollama_network("0.0.0.0"):
                print(f"\n{Colors.GREEN}✅ API is live on LAN at: http://{get_lan_ip()}:11434{Colors.ENDC}")
            input(f"\n{Colors.BOLD}Press Enter to return...{Colors.ENDC}")
        elif choice == '4':
            configure_ollama_network("0.0.0.0") 
            start_open_webui()
            input(f"\n{Colors.BOLD}Press Enter to return...{Colors.ENDC}")
        elif choice == '5':
            launch_cloudflare_tunnel()
        elif choice == '6':
            stop_services()
            input(f"\n{Colors.BOLD}Press Enter to return...{Colors.ENDC}")
        elif choice == '7':
            clear_screen()
            print(f"{Colors.GREEN}👋 Exiting Dashboard...{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"{Colors.WARNING}⚠️ Invalid choice.{Colors.ENDC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.FAIL}🛑 Script interrupted by user. Exiting.{Colors.ENDC}")
        sys.exit(0)
