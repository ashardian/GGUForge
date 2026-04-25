# =============================================================================
# config.py — GGUForge Central Configuration
# All ports, paths, versions, and tunable constants live here.
# =============================================================================

VERSION = "14.0 - Multi-Module Edition"

# --- Model Settings ---
MODEL_EXTENSION = ".gguf"
DEFAULT_MODEL_TEMPERATURE = 0.7
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."

# --- Filesystem ---
SKIP_DIRS = {
    '/proc', '/sys', '/dev', '/run', '/tmp',
    '/var/lib/docker', '/var/lib/containers'
}
EXTERNAL_DRIVE_PATHS = ['/media', '/mnt', '/run/media']

# --- Network Ports ---
OLLAMA_PORT = 11434
WEBUI_PORT = 3000

# --- Docker ---
OPEN_WEBUI_IMAGE = "ghcr.io/open-webui/open-webui:v0.6.5"   # Pinned — not :main
OPEN_WEBUI_CONTAINER_NAME = "open-webui"
WEBUI_STARTUP_WAIT_SECONDS = 15

# --- Ollama ---
OLLAMA_STARTUP_WAIT_SECONDS = 2
OLLAMA_API_BASE = "http://127.0.0.1"

# --- Logging ---
import os
LOG_DIR = os.path.expanduser("~/.gguforge/logs")
LOG_FILE = os.path.join(LOG_DIR, "gguforge.log")
