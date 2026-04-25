# =============================================================================
# tunnel.py — GGUForge Cloudflare WAN Tunnel
# Launches cloudflared quick-tunnel and extracts the public URL from stderr.
# Also saves the last active URL to ~/.gguforge/last_tunnel_url for reference.
# =============================================================================

import os
import re
import subprocess

from config import OLLAMA_PORT, WEBUI_PORT
from ui import Colors, print_header, print_ok, print_warn, print_err, print_info
from ollama_manager import configure_ollama_network
from logger import log

_URL_PATTERN = re.compile(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com')
_LAST_URL_FILE = os.path.expanduser("~/.gguforge/last_tunnel_url")


def _save_tunnel_url(url: str):
    os.makedirs(os.path.dirname(_LAST_URL_FILE), exist_ok=True)
    with open(_LAST_URL_FILE, 'w') as f:
        f.write(url)


def launch_cloudflare_tunnel():
    print_header("☁️  Cloudflare WAN Tunnel")

    print("What do you want to expose to the internet?")
    print(f"  [{Colors.CYAN}1{Colors.ENDC}] Raw Ollama API       (Port {OLLAMA_PORT})")
    print(f"  [{Colors.CYAN}2{Colors.ENDC}] Open WebUI Interface (Port {WEBUI_PORT})")

    choice = input(f"\nSelect [{Colors.CYAN}1-2{Colors.ENDC}]: ").strip()

    if choice == '1':
        port = str(OLLAMA_PORT)
        # Lock Ollama to localhost so only the tunnel can reach the API
        print_warn("Locking Ollama to localhost for secure API tunneling...")
        configure_ollama_network("127.0.0.1")
    elif choice == '2':
        port = str(WEBUI_PORT)
    else:
        print_warn("Invalid choice. Please enter 1 or 2.")
        return

    print_info(f"Starting Cloudflare tunnel on port {port}...")
    print_warn("Press Ctrl+C to close the tunnel.\n")
    print_info("Waiting for tunnel URL...\n")

    process = None
    tunnel_url = None

    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stderr:
            match = _URL_PATTERN.search(line)
            if match and not tunnel_url:
                tunnel_url = match.group(0)
                _save_tunnel_url(tunnel_url)
                log("info", f"Cloudflare tunnel live: {tunnel_url} → port {port}")

                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print(f"{Colors.GREEN}{Colors.BOLD}  ✅ Tunnel is LIVE!{Colors.ENDC}")
                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print(f"\n  🌐 Public URL: {Colors.CYAN}{Colors.UNDERLINE}{tunnel_url}{Colors.ENDC}\n")
                print(f"  📋 URL saved to: {Colors.BOLD}{_LAST_URL_FILE}{Colors.ENDC}")
                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print_warn("Press Ctrl+C to close the tunnel.\n")

        process.wait()

    except KeyboardInterrupt:
        if process:
            process.terminate()
        print(f"\n\n{Colors.GREEN}✅ Tunnel closed safely.{Colors.ENDC}")
        if tunnel_url:
            print_info(f"Last tunnel URL was: {tunnel_url}")
        log("info", "Cloudflare tunnel closed by user.")
