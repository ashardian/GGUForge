# =============================================================================
# services.py — GGUForge Service Controller
# Gracefully stops Ollama and Open WebUI Docker container.
# =============================================================================

import subprocess
from config import OLLAMA_PORT, WEBUI_PORT
from ui import print_header, print_ok, print_warn, print_err
from system import HAS_SUDO, is_installed, get_docker_cmd
from firewall import manage_firewall
from logger import log


def stop_services():
    print_header("🛑 Stopping All Services")

    # --- Ollama ---
    try:
        use_sudo = HAS_SUDO or is_installed("sudo")
        if use_sudo:
            subprocess.run(["sudo", "systemctl", "stop", "ollama"], capture_output=True)
        subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
        manage_firewall("close", str(OLLAMA_PORT))
        print_ok("Ollama stopped.")
        log("info", "Ollama stopped.")
    except Exception as e:
        print_warn(f"Error stopping Ollama: {e}")
        log("warn", f"Error stopping Ollama: {e}")

    # --- Open WebUI ---
    try:
        docker_cmd = get_docker_cmd()
        subprocess.run(
            docker_cmd + ["stop", "open-webui"],
            capture_output=True
        )
        manage_firewall("close", str(WEBUI_PORT))
        print_ok("Open WebUI container stopped.")
        log("info", "Open WebUI stopped.")
    except Exception as e:
        print_warn(f"Error stopping Open WebUI: {e}")
        log("warn", f"Error stopping Open WebUI: {e}")

    print_ok("All services stopped successfully.")
