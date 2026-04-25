# =============================================================================
# ui.py — GGUForge Terminal UI Helpers
# Colors, headers, banners, and formatted print utilities.
# =============================================================================

import os


class Colors:
    HEADER    = '\033[95m'
    BLUE      = '\033[94m'
    CYAN      = '\033[96m'
    GREEN     = '\033[92m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'


def clear_screen():
    os.system('clear')


def print_header(title: str):
    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD} {title}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_separator():
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")


def print_ok(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")


def print_warn(msg: str):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")


def print_err(msg: str):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.ENDC}")


def pause(msg: str = "Press Enter to return..."):
    input(f"\n{Colors.BOLD}{msg}{Colors.ENDC}")
