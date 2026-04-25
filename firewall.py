# =============================================================================
# firewall.py — GGUForge Firewall Manager
# UFW open/close helpers for Ollama and WebUI ports.
# =============================================================================

import subprocess
from system import HAS_SUDO, is_installed
from logger import log


def manage_firewall(action: str = "open", port: str = "11434"):
    """
    Opens or closes a UFW TCP rule for the given port.
    action: 'open' | 'close'
    Silently skips if UFW is not installed or sudo is unavailable.
    """
    if not (HAS_SUDO and is_installed("ufw")):
        return

    if action == "open":
        cmd = ["sudo", "ufw", "allow", f"{port}/tcp"]
        label = f"Opened UFW port {port}/tcp"
    else:
        cmd = ["sudo", "ufw", "delete", "allow", f"{port}/tcp"]
        label = f"Closed UFW port {port}/tcp"

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        log("info", label)
    except subprocess.CalledProcessError as e:
        log("warn", f"UFW rule change failed for port {port}: {e}")
