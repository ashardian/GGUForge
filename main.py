#!/usr/bin/env python3
# =============================================================================
# main.py — GGUForge Entry Point
# Dashboard menu and top-level orchestration.
# Run: python3 main.py
# =============================================================================

import sys

from config import VERSION, OLLAMA_PORT, WEBUI_PORT
from ui import Colors, clear_screen, print_separator, print_ok, print_err, pause
from system import get_lan_ip, get_system_stats, check_sudo_access, HAS_SUDO
from deps import pre_flight_check
from ollama_manager import (
    configure_ollama_network,
    setup_and_run_ollama,
    manage_installed_models,
    pull_model_by_name,
    show_ollama_status,
)
from webui import start_open_webui, show_webui_logs, reset_webui
from tunnel import launch_cloudflare_tunnel
from services import stop_services
from logger import log, get_log_path
from hf_token import manage_hf_token


# ---------------------------------------------------------------------------
# Menu rendering
# ---------------------------------------------------------------------------

def _render_menu():
    stats      = get_system_stats()
    lan_ip     = get_lan_ip()
    perm_label = (
        f"{Colors.GREEN}ROOT CAPABLE{Colors.ENDC}"
        if HAS_SUDO else
        f"{Colors.WARNING}STANDARD USER{Colors.ENDC}"
    )

    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*65}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}  🧠  GGUForge — GGUF Manager & Deployment Dashboard  v{VERSION}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*65}{Colors.ENDC}")
    print(
        f"  {Colors.BOLD}🖥️  IP:{Colors.ENDC}  {Colors.GREEN}{lan_ip}{Colors.ENDC}  │  "
        f"{Colors.BOLD}Mode:{Colors.ENDC} {perm_label}"
    )
    print(
        f"  {Colors.BOLD}💾 RAM:{Colors.ENDC} {Colors.WARNING}{stats['ram']}{Colors.ENDC}  │  "
        f"{Colors.BOLD}Disk:{Colors.ENDC} {Colors.WARNING}{stats['disk']}{Colors.ENDC}  │  "
        f"{Colors.BOLD}CPU:{Colors.ENDC} {Colors.WARNING}{stats['cpu']}{Colors.ENDC}"
    )
    print(f"{Colors.CYAN}{'='*65}{Colors.ENDC}\n")

    items = [
        ("1",  "📦",  "Scan Filesystem & Register .gguf Model"),
        ("2",  "⬇️ ",  "Pull Model by Name (Ollama Registry)"),
        ("3",  "📋",  "Manage / Delete Installed Models"),
        ("4",  "🔍",  "Ollama API Status & Model List"),
        ("5",  "🚀",  f"Start Ollama Backend API       (Port {OLLAMA_PORT})"),
        ("6",  "🌐",  f"Start Open WebUI Dashboard     (Port {WEBUI_PORT})"),
        ("7",  "📋",  "View Open WebUI Live Logs"),
        ("8",  "☁️ ",  "Launch WAN Tunnel (Cloudflare)"),
        ("9",  "🛑",  "Stop All Services"),
        ("10", "🔄",  "Reset Open WebUI  (wipe container + accounts)"),
        ("11", "🔑",  "Manage HuggingFace Token"),
        ("12", "📄",  f"View Log File  ({get_log_path()})"),
        ("0",  "❌",  "Exit"),
    ]

    for key, icon, label in items:
        color = Colors.FAIL if key == "0" else Colors.CYAN
        print(f"  [{color}{key:>2}{Colors.ENDC}] {icon}  {label}")

    print()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    try:
        pre_flight_check()
        check_sudo_access()
        log("info", f"GGUForge v{VERSION} started.")
    except KeyboardInterrupt:
        sys.exit(0)

    while True:
        _render_menu()

        try:
            choice = input(f"  Select action [{Colors.CYAN}0-12{Colors.ENDC}]: ").strip()
        except KeyboardInterrupt:
            choice = "0"

        if choice == '1':
            setup_and_run_ollama()
            pause()

        elif choice == '2':
            pull_model_by_name()
            pause()

        elif choice == '3':
            manage_installed_models()
            pause()

        elif choice == '4':
            show_ollama_status()
            pause()

        elif choice == '5':
            if configure_ollama_network("0.0.0.0"):
                print_ok(f"API is live on LAN at: http://{get_lan_ip()}:{OLLAMA_PORT}")
            pause()

        elif choice == '6':
            configure_ollama_network("0.0.0.0")
            start_open_webui()
            pause()

        elif choice == '7':
            show_webui_logs()
            pause()

        elif choice == '8':
            launch_cloudflare_tunnel()

        elif choice == '9':
            stop_services()
            pause()

        elif choice == '10':
            reset_webui()
            pause()

        elif choice == '11':
            manage_hf_token()
            pause()

        elif choice == '12':
            log_path = get_log_path()
            try:
                with open(log_path) as f:
                    lines = f.readlines()
                clear_screen()
                print(f"{Colors.BOLD}--- Last 40 log entries ({log_path}) ---{Colors.ENDC}\n")
                for line in lines[-40:]:
                    print(line, end="")
            except FileNotFoundError:
                print_err("Log file not found yet.")
            pause()

        elif choice == '0':
            clear_screen()
            print(f"{Colors.GREEN}👋 GGUForge exiting. Goodbye.{Colors.ENDC}\n")
            log("info", "GGUForge exited cleanly.")
            sys.exit(0)

        else:
            import time
            print_err("Invalid choice. Enter a number 0–12.")
            import time; time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.FAIL}🛑 Interrupted by user. Exiting.{Colors.ENDC}")
        sys.exit(0)
