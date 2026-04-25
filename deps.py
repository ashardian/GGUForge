# =============================================================================
# deps.py — GGUForge Dependency Manager
# Pre-flight checks and optional auto-installation for Ollama, Docker,
# Cloudflared, and curl.
# =============================================================================

import subprocess
import sys
import time

from ui import Colors, print_header, print_separator, print_ok, print_warn, print_err, print_info, pause
from system import is_installed, check_sudo_access
from logger import log


# ---------------------------------------------------------------------------
# Individual installers
# ---------------------------------------------------------------------------

def _install_ollama():
    print_info("The installer may ask for your sudo password.")
    try:
        subprocess.run(
            "curl -fsSL https://ollama.com/install.sh | sh",
            shell=True, check=True
        )
        log("info", "Ollama installed successfully.")
        time.sleep(1)
    except subprocess.CalledProcessError:
        print_err("The Ollama installation script failed.")
        log("error", "Ollama installation script returned non-zero.")
    except KeyboardInterrupt:
        print_err("Installation aborted by user.")


def _install_docker():
    print_info("The installer may ask for your sudo password.")
    try:
        subprocess.run(
            "curl -fsSL https://get.docker.com | sh",
            shell=True, check=True
        )
        log("info", "Docker installed successfully.")
        time.sleep(1)
    except subprocess.CalledProcessError:
        print_err("The Docker installation script failed.")
        log("error", "Docker installation script returned non-zero.")
    except KeyboardInterrupt:
        print_err("Docker installation aborted.")


def _install_cloudflared():
    deb_url = (
        "https://github.com/cloudflare/cloudflared/releases/latest"
        "/download/cloudflared-linux-amd64.deb"
    )
    try:
        subprocess.run(
            f'curl -L --output /tmp/cloudflared.deb "{deb_url}"',
            shell=True, check=True
        )
        subprocess.run(
            ["sudo", "dpkg", "-i", "/tmp/cloudflared.deb"],
            check=True
        )
        log("info", "Cloudflared installed successfully.")
        time.sleep(1)
    except subprocess.CalledProcessError:
        print_err("Cloudflared installation failed.")
        log("error", "Cloudflared dpkg install returned non-zero.")
    except KeyboardInterrupt:
        print_err("Cloudflared installation aborted.")


# ---------------------------------------------------------------------------
# Public pre-flight check
# ---------------------------------------------------------------------------

def pre_flight_check():
    print_header("🛫 Running Pre-Flight Checks")
    check_sudo_access()

    # curl is mandatory — no interactive install, just bail
    if not is_installed("curl"):
        print_err("'curl' is missing. Install it manually (e.g., sudo apt install curl) and restart.")
        log("error", "Pre-flight: curl not found. Exiting.")
        sys.exit(1)

    # Ollama — optional install prompt
    if not is_installed("ollama"):
        print_warn("Ollama is not installed. This is required for core functionality.")
        if input("Install Ollama now? (y/N): ").strip().lower() == 'y':
            _install_ollama()

    # Docker — optional install prompt
    if not is_installed("docker"):
        print_warn("Docker is not installed (required for Open WebUI).")
        if input("Install Docker now? (y/N): ").strip().lower() == 'y':
            _install_docker()

    # Cloudflared — optional install prompt
    if not is_installed("cloudflared"):
        print_warn("Cloudflared is not installed (required for WAN tunnels).")
        if input("Install Cloudflared now? (y/N): ").strip().lower() == 'y':
            _install_cloudflared()

    # --- Status Report ---
    print_header("📊 Dependency Status Report")

    def _status(cmd: str) -> str:
        ok = is_installed(cmd)
        log("info", f"Dependency check: {cmd} → {'OK' if ok else 'MISSING'}")
        return (
            f"{Colors.GREEN}✅ Installed{Colors.ENDC}"
            if ok else
            f"{Colors.FAIL}❌ Missing{Colors.ENDC}"
        )

    print(f" {Colors.BOLD}• Curl:{Colors.ENDC}         {_status('curl')}")
    print(f" {Colors.BOLD}• Ollama:{Colors.ENDC}       {_status('ollama')}")
    print(f" {Colors.BOLD}• Docker:{Colors.ENDC}       {_status('docker')}")
    print(f" {Colors.BOLD}• Cloudflared:{Colors.ENDC}  {_status('cloudflared')}")
    print_separator()

    if not is_installed("ollama"):
        print_warn("Ollama is missing. Most features will fail to launch.")

    pause("Press [Enter] to proceed to the Dashboard...")
