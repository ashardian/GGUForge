# =============================================================================
# webui.py — GGUForge Open WebUI Manager
# Handles Docker container lifecycle for Open WebUI, including RAG embedding
# engine override, stable secret key, and crash diagnostics.
# =============================================================================

import os
import secrets
import subprocess

from config import (
    OPEN_WEBUI_IMAGE, OPEN_WEBUI_CONTAINER_NAME,
    WEBUI_PORT, OLLAMA_PORT, WEBUI_STARTUP_WAIT_SECONDS
)
from ui import Colors, print_header, print_ok, print_warn, print_err, print_info
from system import get_lan_ip, get_docker_cmd
from firewall import manage_firewall
from logger import log
import time

_GGUFORGE_DIR    = os.path.expanduser("~/.gguforge")
_SECRET_KEY_FILE = os.path.join(_GGUFORGE_DIR, "webui_secret_key")
_FIRST_RUN_FLAG  = os.path.join(_GGUFORGE_DIR, "webui_first_run_done")


def _get_or_create_secret_key() -> str:
    """
    Generates a 64-char hex secret key on first call and saves it to
    ~/.gguforge/webui_secret_key. Reuses it on every subsequent launch so
    that user sessions and password hashes survive container rebuilds.
    """
    os.makedirs(_GGUFORGE_DIR, exist_ok=True)
    if os.path.exists(_SECRET_KEY_FILE):
        with open(_SECRET_KEY_FILE) as f:
            key = f.read().strip()
        if key:
            return key
    key = secrets.token_hex(32)
    with open(_SECRET_KEY_FILE, 'w') as f:
        f.write(key)
    os.chmod(_SECRET_KEY_FILE, 0o600)
    log("info", "Generated new WEBUI_SECRET_KEY and saved to disk.")
    return key


def _is_first_run() -> bool:
    return not os.path.exists(_FIRST_RUN_FLAG)


def _mark_first_run_done():
    os.makedirs(_GGUFORGE_DIR, exist_ok=True)
    with open(_FIRST_RUN_FLAG, 'w') as f:
        f.write("done")


def _container_exists(docker_cmd: list) -> bool:
    result = subprocess.run(
        docker_cmd + ["ps", "-a", "-q", "-f", f"name={OPEN_WEBUI_CONTAINER_NAME}"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def _container_is_running(docker_cmd: list) -> bool:
    result = subprocess.run(
        docker_cmd + [
            "inspect", "-f", "{{.State.Running}}",
            OPEN_WEBUI_CONTAINER_NAME
        ],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "true"


def _get_hf_token() -> str:
    """
    Reads HF_TOKEN from environment or ~/.gguforge/hf_token file.
    Returns empty string if not set — Open WebUI still works without it.
    """
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        token_file = os.path.expanduser("~/.gguforge/hf_token")
        if os.path.exists(token_file):
            with open(token_file) as f:
                token = f.read().strip()
    return token


def start_open_webui():
    print_header("🖥️  Open WebUI (Docker)")

    docker_cmd = get_docker_cmd()

    if not _is_docker_available(docker_cmd):
        print_err("Docker is not installed or not accessible on this system.")
        return

    try:
        if _container_exists(docker_cmd):
            print_info(f"Starting existing '{OPEN_WEBUI_CONTAINER_NAME}' container...")
            subprocess.run(
                docker_cmd + ["start", OPEN_WEBUI_CONTAINER_NAME],
                check=True
            )
            log("info", f"Started existing Open WebUI container.")
        else:
            hf_token   = _get_hf_token()
            secret_key = _get_or_create_secret_key()
            first_run  = _is_first_run()

            print_info(
                f"Pulling and creating Open WebUI container ({OPEN_WEBUI_IMAGE}).\n"
                "This may take several minutes on first run..."
            )
            cmd = docker_cmd + [
                "run", "-d",
                "-p", f"{WEBUI_PORT}:8080",
                "--add-host=host.docker.internal:host-gateway",
                "-e", f"OLLAMA_BASE_URL=http://host.docker.internal:{OLLAMA_PORT}",
                "-e", "HF_ENDPOINT=https://hf-mirror.com",
                # Disable HuggingFace sentence-transformer downloads — use Ollama
                # for embeddings instead. Prevents the 500 error on RAG init.
                "-e", "RAG_EMBEDDING_ENGINE=ollama",
                "-e", f"RAG_OLLAMA_BASE_URL=http://host.docker.internal:{OLLAMA_PORT}",
                # Stable secret key — ensures sessions and password hashes survive
                # container rebuilds. Without this, every new container invalidates
                # all existing accounts.
                "-e", f"WEBUI_SECRET_KEY={secret_key}",
            ]
            if hf_token:
                cmd += ["-e", f"HF_TOKEN={hf_token}"]
                print_info("HuggingFace token detected — injecting into container.")
            else:
                print_warn(
                    "No HF_TOKEN found. Save your token to ~/.gguforge/hf_token "
                    "or export HF_TOKEN=... to enable gated models."
                )

            cmd += [
                "-v", "open-webui:/app/backend/data",
                "--name", OPEN_WEBUI_CONTAINER_NAME,
                "--restart", "always",
                OPEN_WEBUI_IMAGE,
            ]
            subprocess.run(cmd, check=True)
            log("info", f"Created new Open WebUI container from {OPEN_WEBUI_IMAGE}")

            if first_run:
                _mark_first_run_done()
                print(f"\n{Colors.WARNING}{'='*60}{Colors.ENDC}")
                print(f"{Colors.WARNING}{Colors.BOLD}  ⚠️  FIRST-RUN — IMPORTANT{Colors.ENDC}")
                print(f"{Colors.WARNING}{'='*60}{Colors.ENDC}")
                print(f"  {Colors.BOLD}When the WebUI opens:{Colors.ENDC}")
                print(f"  {Colors.GREEN}1.{Colors.ENDC} Click  ➜  {Colors.CYAN}{Colors.BOLD}Sign Up{Colors.ENDC}  (NOT Sign In)")
                print(f"  {Colors.GREEN}2.{Colors.ENDC} Create your admin account")
                print(f"  {Colors.GREEN}3.{Colors.ENDC} All future logins use Sign In")
                print(f"\n  {Colors.WARNING}Going straight to Sign In on first run")
                print(f"  will always fail — no accounts exist yet.{Colors.ENDC}")
                print(f"{Colors.WARNING}{'='*60}{Colors.ENDC}\n")

        # --- Stability check via polling instead of fixed sleep ---
        print_info(f"Verifying container stability (up to {WEBUI_STARTUP_WAIT_SECONDS}s)...")
        for i in range(WEBUI_STARTUP_WAIT_SECONDS):
            time.sleep(1)
            if _container_is_running(docker_cmd):
                break
        
        if not _container_is_running(docker_cmd):
            print_err("FATAL: Open WebUI container crashed immediately after starting.")
            print_warn(
                "Common causes: Out-Of-Memory (low RAM), corrupted Docker volumes, "
                "or a port conflict on 3000."
            )
            print(f"\n{Colors.BOLD}--- Crash Logs (Last 20 lines) ---{Colors.ENDC}")
            logs_result = subprocess.run(
                docker_cmd + ["logs", "--tail", "20", OPEN_WEBUI_CONTAINER_NAME],
                capture_output=True, text=True
            )
            print(f"{Colors.FAIL}{logs_result.stderr or logs_result.stdout}{Colors.ENDC}")
            print("----------------------------------\n")
            log("error", "Open WebUI container crashed on startup.")
            return

        manage_firewall("open", str(WEBUI_PORT))
        lan_ip = get_lan_ip()

        print_ok("Docker container is running and stable!")
        print(
            f"\n  {Colors.CYAN}{Colors.BOLD}"
            f"Local:   http://{lan_ip}:{WEBUI_PORT}{Colors.ENDC}"
        )
        print(
            f"  {Colors.WARNING}Note: WebUI backend takes 1–3 minutes to fully initialize.\n"
            f"  If the page shows 'Cannot be reached', wait 60 seconds and refresh.{Colors.ENDC}"
        )
        log("info", f"Open WebUI stable at http://{lan_ip}:{WEBUI_PORT}")

    except subprocess.CalledProcessError as e:
        print_err(f"Docker execution failed: {e}")
        print_warn("Ensure your user is in the 'docker' group or run with sudo.")
        log("error", f"start_open_webui CalledProcessError: {e}")


def _is_docker_available(docker_cmd: list) -> bool:
    try:
        subprocess.run(
            docker_cmd + ["info"],
            capture_output=True, check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def reset_webui():
    """
    Wipes the Open WebUI container and its data volume so the user can start
    fresh with a clean Sign Up. Secret key is preserved so a new account works
    immediately without further configuration.
    """
    print_header("🔄 Reset Open WebUI")
    print_warn("This will DELETE the Open WebUI container and ALL account data.")
    print_warn("Your Ollama models are NOT affected.")
    confirm = input(
        f"\n  Type {Colors.FAIL}{Colors.BOLD}RESET{Colors.ENDC} to confirm, "
        "or press Enter to cancel: "
    ).strip()

    if confirm != "RESET":
        print_info("Reset cancelled.")
        return

    docker_cmd = get_docker_cmd()
    try:
        subprocess.run(docker_cmd + ["stop",   "open-webui"],       capture_output=True)
        subprocess.run(docker_cmd + ["rm",     "open-webui"],       capture_output=True)
        subprocess.run(docker_cmd + ["volume", "rm", "open-webui"], capture_output=True)

        # Remove the first-run flag so the signup notice shows again on next launch
        if os.path.exists(_FIRST_RUN_FLAG):
            os.remove(_FIRST_RUN_FLAG)

        print_ok("Open WebUI wiped successfully.")
        print_info("Launch Option 6 to create a fresh container.")
        print_info("On the first page, click  ➜  Sign Up  to create your admin account.")
        log("info", "Open WebUI container and volume reset by user.")
    except Exception as e:
        print_err(f"Reset failed: {e}")
        log("error", f"reset_webui exception: {e}")


def show_webui_logs(lines: int = 30):
    """Tail live logs from the Open WebUI container."""
    print_header("📋 Open WebUI — Live Logs")
    docker_cmd = get_docker_cmd()
    print_warn("Press Ctrl+C to stop log stream.\n")
    try:
        subprocess.run(
            docker_cmd + ["logs", "--tail", str(lines), "-f", OPEN_WEBUI_CONTAINER_NAME]
        )
    except KeyboardInterrupt:
        print_info("Log stream stopped.")
    except subprocess.CalledProcessError:
        print_err("Could not fetch logs. Is the container running?")
