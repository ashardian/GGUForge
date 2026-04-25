# =============================================================================
# system.py — GGUForge System Utilities
# Binary detection, LAN IP, RAM/disk stats, sudo capability.
# =============================================================================

import os
import shutil
import socket
import subprocess

# Module-level sudo flag — set once by check_sudo_access(), read everywhere.
HAS_SUDO: bool = False


def is_installed(tool: str) -> bool:
    """
    Bulletproof binary check. Searches PATH via shutil.which() then falls back
    to a list of common install locations to handle stale PATH environments.
    """
    if shutil.which(tool):
        return True
    common_paths = [
        f"/usr/local/bin/{tool}",
        f"/usr/bin/{tool}",
        f"/bin/{tool}",
        f"/opt/bin/{tool}",
        os.path.expanduser(f"~/.local/bin/{tool}"),
    ]
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    return False


def check_sudo_access() -> bool:
    """
    Tests passwordless sudo. Updates the global HAS_SUDO flag and returns it.
    """
    global HAS_SUDO
    try:
        subprocess.run(
            ["sudo", "-n", "true"],
            check=True,
            capture_output=True
        )
        HAS_SUDO = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        HAS_SUDO = False
    return HAS_SUDO


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_system_stats() -> dict:
    stats = {"ram": "Unknown", "disk": "Unknown", "cpu": "Unknown"}

    # RAM — available from /proc/meminfo
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total_kb = next(
            int(l.split()[1]) for l in lines if l.startswith("MemTotal")
        )
        avail_kb = next(
            int(l.split()[1]) for l in lines if l.startswith("MemAvailable")
        )
        used_gb  = (total_kb - avail_kb) / (1024 ** 2)
        total_gb = total_kb / (1024 ** 2)
        stats["ram"] = f"{used_gb:.1f}/{total_gb:.1f} GB"
    except Exception:
        pass

    # Disk — root partition free space
    try:
        total, used, free = shutil.disk_usage("/")
        stats["disk"] = f"{free / (1024**3):.1f} GB Free"
    except Exception:
        pass

    # CPU core count
    try:
        cpu_count = os.cpu_count() or "?"
        stats["cpu"] = f"{cpu_count} cores"
    except Exception:
        pass

    return stats


def get_docker_cmd() -> list:
    """Returns the appropriate docker command prefix based on sudo availability."""
    use_sudo = HAS_SUDO or is_installed("sudo")
    return ["sudo", "docker"] if use_sudo else ["docker"]
