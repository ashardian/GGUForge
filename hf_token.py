# =============================================================================
# hf_token.py — GGUForge HuggingFace Token Manager
# Save, view, test, and delete your HF token from inside the dashboard.
# Token is stored at ~/.gguforge/hf_token (chmod 600).
# =============================================================================

import os
import urllib.request
import urllib.error
import json

from ui import Colors, print_header, print_ok, print_warn, print_err, print_info
from logger import log

_GGUFORGE_DIR  = os.path.expanduser("~/.gguforge")
_TOKEN_FILE    = os.path.join(_GGUFORGE_DIR, "hf_token")
_HF_API_WHOAMI = "https://huggingface.co/api/whoami-v2"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_token() -> str:
    if os.path.exists(_TOKEN_FILE):
        with open(_TOKEN_FILE) as f:
            return f.read().strip()
    return ""


def _write_token(token: str):
    os.makedirs(_GGUFORGE_DIR, exist_ok=True)
    with open(_TOKEN_FILE, 'w') as f:
        f.write(token)
    os.chmod(_TOKEN_FILE, 0o600)


def _mask_token(token: str) -> str:
    """Shows first 6 and last 4 chars, masks the middle."""
    if len(token) <= 10:
        return "****"
    return f"{token[:6]}{'*' * (len(token) - 10)}{token[-4:]}"


def _test_token(token: str) -> tuple[bool, str]:
    """
    Validates the token against HuggingFace API.
    Returns (success: bool, username_or_error: str).
    """
    try:
        req = urllib.request.Request(
            _HF_API_WHOAMI,
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            return True, data.get("name", "unknown")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid token (401 Unauthorized)"
        return False, f"HTTP error {e.code}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Public menu
# ---------------------------------------------------------------------------

def manage_hf_token():
    print_header("🔑 HuggingFace Token Manager")

    current = _read_token()

    if current:
        print(f"  {Colors.BOLD}Current token:{Colors.ENDC} "
              f"{Colors.CYAN}{_mask_token(current)}{Colors.ENDC}")
    else:
        print_warn("No token saved yet.")

    print(f"\n  [{Colors.CYAN}1{Colors.ENDC}] Save / Update token")
    print(f"  [{Colors.CYAN}2{Colors.ENDC}] Test current token against HuggingFace API")
    print(f"  [{Colors.CYAN}3{Colors.ENDC}] Show token path info")
    print(f"  [{Colors.CYAN}4{Colors.ENDC}] Delete saved token")
    print(f"  [{Colors.CYAN}0{Colors.ENDC}] Back to dashboard\n")

    choice = input(f"  Select [{Colors.CYAN}0-4{Colors.ENDC}]: ").strip()

    if choice == '1':
        _save_token_flow()

    elif choice == '2':
        _test_token_flow(current)

    elif choice == '3':
        _show_token_info(current)

    elif choice == '4':
        _delete_token_flow(current)

    elif choice == '0':
        return

    else:
        print_warn("Invalid choice.")


def _save_token_flow():
    print_info("Get your token at: https://huggingface.co/settings/tokens")
    print_info("Required scope: 'Read' (for public gated models) or 'Write' (for uploads)\n")

    token = input("  Paste your HF token (input hidden by shell): ").strip()

    if not token:
        print_warn("No token entered. Cancelled.")
        return

    if not token.startswith("hf_"):
        print_warn("Token doesn't start with 'hf_' — double-check you copied the full token.")
        if input("  Save anyway? (y/N): ").strip().lower() != 'y':
            return

    print_info("Validating token against HuggingFace API...")
    ok, result = _test_token(token)

    if ok:
        _write_token(token)
        print_ok(f"Token validated ✓  Logged in as: {Colors.CYAN}{result}{Colors.ENDC}")
        print_ok(f"Saved to: {_TOKEN_FILE}")
        log("info", f"HF token saved and validated for user '{result}'.")
    else:
        print_warn(f"Validation failed: {result}")
        if input("  Save token anyway? (y/N): ").strip().lower() == 'y':
            _write_token(token)
            print_ok(f"Token saved (unvalidated) to: {_TOKEN_FILE}")
            log("warn", f"HF token saved without successful validation: {result}")
        else:
            print_info("Token not saved.")


def _test_token_flow(current: str):
    if not current:
        print_err("No token saved. Use option 1 to save one first.")
        return

    print_info("Testing token against HuggingFace API...")
    ok, result = _test_token(current)

    if ok:
        print_ok(f"Token is valid ✓  Logged in as: {Colors.CYAN}{result}{Colors.ENDC}")
        log("info", f"HF token test passed for user '{result}'.")
    else:
        print_err(f"Token test failed: {result}")
        log("warn", f"HF token test failed: {result}")


def _show_token_info(current: str):
    print(f"\n  {Colors.BOLD}Token file:{Colors.ENDC}  {_TOKEN_FILE}")
    print(f"  {Colors.BOLD}Exists:{Colors.ENDC}      {'Yes' if current else 'No'}")
    if current:
        print(f"  {Colors.BOLD}Masked:{Colors.ENDC}      {_mask_token(current)}")
        perms = oct(os.stat(_TOKEN_FILE).st_mode)[-3:]
        print(f"  {Colors.BOLD}Permissions:{Colors.ENDC} {perms}  "
              f"{'✅ Secure' if perms == '600' else '⚠️  Should be 600'}")
    print(f"\n  {Colors.BOLD}Used by:{Colors.ENDC}     Open WebUI (injected on container create)")
    print(f"  {Colors.WARNING}Note: Re-launch Open WebUI (Option 6) after changing token.{Colors.ENDC}\n")


def _delete_token_flow(current: str):
    if not current:
        print_err("No token saved — nothing to delete.")
        return

    confirm = input(
        f"  {Colors.FAIL}Delete saved HF token? (y/N):{Colors.ENDC} "
    ).strip().lower()

    if confirm == 'y':
        os.remove(_TOKEN_FILE)
        print_ok("Token deleted.")
        log("info", "HF token deleted by user.")
    else:
        print_info("Deletion cancelled.")
