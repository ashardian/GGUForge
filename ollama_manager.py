# =============================================================================
# ollama_manager.py — GGUForge Ollama Manager
# Network configuration, GGUF model registration, model list/delete,
# pull-by-name, and Ollama API status check.
# =============================================================================

import os
import re
import subprocess
import time
import urllib.request
import urllib.error
import json

from config import (
    OLLAMA_PORT, OLLAMA_STARTUP_WAIT_SECONDS,
    DEFAULT_MODEL_TEMPERATURE, DEFAULT_SYSTEM_PROMPT,
    EXTERNAL_DRIVE_PATHS
)
from ui import Colors, print_header, print_ok, print_warn, print_err, print_info
from system import HAS_SUDO, is_installed
from firewall import manage_firewall
from scanner import find_gguf_models
from logger import log


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ollama_api_alive(host: str = "127.0.0.1") -> bool:
    """Returns True if Ollama's REST API is responding."""
    try:
        with urllib.request.urlopen(
            f"http://{host}:{OLLAMA_PORT}/api/tags", timeout=4
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


def _poll_ollama_ready(host: str = "127.0.0.1", timeout: int = 30) -> bool:
    """Polls Ollama API every second until it responds or timeout expires."""
    for _ in range(timeout):
        if _ollama_api_alive(host):
            return True
        time.sleep(1)
    return False


# ---------------------------------------------------------------------------
# Network configuration
# ---------------------------------------------------------------------------

def configure_ollama_network(host: str = "0.0.0.0") -> bool:
    """
    Writes a systemd override to set OLLAMA_HOST, reloads and restarts the
    service. Falls back to a direct Popen if systemd is unavailable.
    """
    print_info(f"Routing Ollama backend to {host}:{OLLAMA_PORT}...")
    log("info", f"configure_ollama_network called with host={host}")

    use_sudo = HAS_SUDO or is_installed("sudo")
    if use_sudo:
        override_dir  = "/etc/systemd/system/ollama.service.d"
        override_file = os.path.join(override_dir, "override.conf")
        service_config = f'[Service]\nEnvironment="OLLAMA_HOST={host}"\n'
        try:
            subprocess.run(["sudo", "mkdir", "-p", override_dir], check=True)
            subprocess.run(
                ["sudo", "tee", override_file],
                input=service_config,
                capture_output=True,
                text=True,
                check=True
            )
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "ollama"], check=True)

            if host == "0.0.0.0":
                manage_firewall("open", str(OLLAMA_PORT))

            # Poll instead of fixed sleep
            print_info("Waiting for Ollama API to become ready...")
            if _poll_ollama_ready(timeout=30):
                print_ok("Ollama API is live.")
                log("info", f"Ollama started successfully on {host}:{OLLAMA_PORT}")
                return True
            else:
                print_warn("Ollama did not respond within 30 seconds.")
                log("warn", "Ollama poll timeout after systemd restart.")
                return False

        except subprocess.CalledProcessError as e:
            print_warn(f"Systemd configuration failed ({e}). Falling back to local mode.")
            log("warn", f"systemd Ollama config failed: {e}")

    # Fallback — direct process
    print_warn("Starting lightweight local server instance...")
    try:
        subprocess.run(["pkill", "ollama"], capture_output=True)
        env = os.environ.copy()
        env["OLLAMA_HOST"] = host
        subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print_info("Waiting for Ollama API to become ready...")
        if _poll_ollama_ready(timeout=30):
            print_ok("Ollama API is live.")
            log("info", f"Ollama started via Popen on {host}:{OLLAMA_PORT}")
            return True
        else:
            print_warn("Ollama did not respond within 30 seconds.")
            log("warn", "Ollama poll timeout after Popen fallback.")
            return False
    except Exception as e:
        print_err(f"Failed to start local server: {e}")
        log("error", f"Ollama Popen fallback failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Ollama API status check
# ---------------------------------------------------------------------------

def show_ollama_status():
    print_header("🔍 Ollama API Status")
    alive = _ollama_api_alive()
    if alive:
        print_ok(f"Ollama is running at http://127.0.0.1:{OLLAMA_PORT}")
        # List running models via API
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{OLLAMA_PORT}/api/tags", timeout=4
            ) as resp:
                data = json.loads(resp.read())
            models = data.get("models", [])
            if models:
                print(f"\n  {Colors.BOLD}Registered models:{Colors.ENDC}")
                for m in models:
                    size_gb = m.get("size", 0) / (1024**3)
                    print(f"    {Colors.CYAN}•{Colors.ENDC} {m['name']}  "
                          f"{Colors.WARNING}({size_gb:.1f} GB){Colors.ENDC}")
            else:
                print_info("No models registered yet.")
        except Exception:
            pass
    else:
        print_err(f"Ollama is NOT responding on port {OLLAMA_PORT}.")
        print_info("Start it from the dashboard (Option 3) or run: ollama serve")
    log("info", f"Ollama status check: {'alive' if alive else 'dead'}")


# ---------------------------------------------------------------------------
# GGUF scan → Ollama register
# ---------------------------------------------------------------------------

def setup_and_run_ollama():
    print_header("🔍 GGUF Model Scanner")
    search_paths = []

    if input("Scan external drives (USB/HDD)? (y/N): ").strip().lower() == 'y':
        search_paths.extend(EXTERNAL_DRIVE_PATHS)

    scan_choice = input(
        "Press [Enter] to scan Home, or type 'root' to scan entire system (/): "
    ).strip().lower()
    search_paths.append("/" if scan_choice == 'root' else os.path.expanduser("~"))

    print_info("Scanning filesystem for .gguf files...")
    models = find_gguf_models(search_paths)

    if not models:
        print_err("No .gguf models found in the selected paths.")
        return

    print(f"\n{Colors.BOLD}--- Found Models ({len(models)}) ---{Colors.ENDC}")
    for i, m in enumerate(models):
        print(
            f"  [{Colors.CYAN}{i+1}{Colors.ENDC}] "
            f"{Colors.BOLD}{m['name']}{Colors.ENDC}  "
            f"{Colors.WARNING}{m['size']}{Colors.ENDC}\n"
            f"       {m['path']}"
        )

    try:
        choice = input(
            f"\nSelect a model [{Colors.CYAN}1-{len(models)}{Colors.ENDC}] "
            "or 'q' to cancel: "
        ).strip().lower()
        if choice == 'q':
            return
        target = models[int(choice) - 1]
    except (ValueError, IndexError):
        print_warn("Invalid selection.")
        return

    default_name = (
        f"{os.path.splitext(target['name'])[0].lower()}:community"
    )
    name_input  = input(f"\nCustom name for Ollama registry (default: {default_name}): ").strip()
    model_name  = name_input if name_input else default_name

    # Prompt customization
    temp_input  = input(f"Temperature (default {DEFAULT_MODEL_TEMPERATURE}): ").strip()
    temperature = float(temp_input) if temp_input else DEFAULT_MODEL_TEMPERATURE
    sys_prompt  = input(f"System prompt (default: '{DEFAULT_SYSTEM_PROMPT}'): ").strip()
    if not sys_prompt:
        sys_prompt = DEFAULT_SYSTEM_PROMPT

    modelfile_path = os.path.join(os.path.dirname(target["path"]), "Modelfile_temp")
    try:
        with open(modelfile_path, 'w') as f:
            f.write(
                f'FROM "{target["path"]}"\n'
                f'PARAMETER temperature {temperature}\n'
                f'SYSTEM "{sys_prompt}"\n'
            )
        print_info(f"Building '{model_name}' in Ollama. Please wait...")
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", modelfile_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print_ok(f"Built successfully! '{model_name}' is ready for inference.")
            log("info", f"Registered GGUF model '{model_name}' from {target['path']}")
        else:
            print_err(f"Ollama create failed:\n{result.stderr}")
            log("error", f"ollama create failed for '{model_name}': {result.stderr}")
    except Exception as e:
        print_err(f"Error: {e}")
        log("error", f"setup_and_run_ollama exception: {e}")
    finally:
        if os.path.exists(modelfile_path):
            os.remove(modelfile_path)


# ---------------------------------------------------------------------------
# Pull model by name from Ollama registry
# ---------------------------------------------------------------------------

def pull_model_by_name():
    print_header("⬇️  Pull Model from Ollama Registry")
    print_info("Browse available models at: https://ollama.com/library")
    model_name = input("\nEnter model name to pull (e.g. llama3, mistral, qwen2.5:3b): ").strip()

    if not model_name:
        print_warn("No model name entered. Cancelled.")
        return

    if not re.match(r'^[a-zA-Z0-9_\-\.:]+$', model_name):
        print_err("Invalid model name. Only letters, numbers, hyphens, underscores, dots, and colons allowed.")
        return

    print_info(f"Pulling '{model_name}'... (This may take a while for large models)")
    log("info", f"Pulling model '{model_name}' from Ollama registry.")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print_ok(f"'{model_name}' pulled and ready.")
        log("info", f"Model '{model_name}' pulled successfully.")
    except subprocess.CalledProcessError as e:
        print_err(f"Pull failed: {e}")
        log("error", f"ollama pull failed for '{model_name}': {e}")


# ---------------------------------------------------------------------------
# List and delete installed models
# ---------------------------------------------------------------------------

def manage_installed_models():
    print_header("📦 Installed Ollama Models")
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            print(result.stdout)
        else:
            print_info("No models installed yet.")
            return

        del_choice = input(
            f"\n{Colors.WARNING}Type a model name to DELETE it, "
            f"or press Enter to return:{Colors.ENDC} "
        ).strip()

        if del_choice:
            if not re.match(r'^[a-zA-Z0-9_\-\.:]+$', del_choice):
                print_err("Invalid model name. Only letters, numbers, hyphens, underscores, dots, and colons are allowed.")
                return
            confirm = input(f"Are you sure you want to delete '{del_choice}'? (y/N): ").strip().lower()
            if confirm == 'y':
                subprocess.run(["ollama", "rm", del_choice])
                print_ok(f"Model '{del_choice}' deleted.")
                log("info", f"Deleted model '{del_choice}'")
            else:
                print_info("Deletion cancelled.")

    except subprocess.CalledProcessError:
        print_err("Could not fetch models. Is Ollama running?")
        log("error", "manage_installed_models: ollama list failed.")
