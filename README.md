
# 🧠 GGUF Manager & Deployment Dashboard

> **v13.0 – Diagnostic Edition** > A terminal-based management suite for running, deploying, and exposing local LLMs via Ollama — with an integrated Open WebUI interface and Cloudflare WAN tunneling.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Menu Options](#menu-options)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Hugging Face Integration](#hugging-face-integration)
- [Security Notes](#security-notes)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)

---

## Overview

**GGUF Manager** is a single-file Python CLI tool that turns a Linux machine into a fully functional local LLM server — no cloud required. It automates the entire pipeline: scanning your filesystem for `.gguf` model files, registering them with Ollama, launching a browser-based chat UI via Docker, and optionally exposing everything to the internet through a zero-config Cloudflare tunnel.

Designed for self-hosters, privacy-conscious users, and AI hobbyists who want full control over their models without touching a cloud API.

---

## Features

### 🔍 GGUF Model Scanner
- Recursively scans your **home directory**, **entire filesystem (`/`)**, or **external drives** (USB/HDD via `/media`, `/mnt`, `/run/media`) for `.gguf` model files.
- Safely skips system directories (`/proc`, `/sys`, `/dev`, `/run`, `/tmp`, `/var/lib/docker`, etc.) to avoid hangs or permission errors.
- Presents a numbered list of discovered models for easy selection.
- Auto-generates a default Ollama registry name from the filename (e.g. `mistral-7b-q4_k_m:community`).
- Allows custom naming before registration.
- Writes a temporary `Modelfile` with sensible defaults (`temperature 0.7`, a default system prompt) and cleans it up after use.

### 📦 Ollama Model Manager
- Lists all models currently registered in Ollama (`ollama list`).
- Allows deletion of registered models directly from the dashboard.
- Input validation on model names — only safe characters (`a-z`, `0-9`, `-`, `_`, `.`, `:`) are accepted to prevent command injection.

### 🚀 Backend API Server (Port 11434)
- Configures Ollama to bind on `0.0.0.0` (LAN-accessible) via a **systemd override** (`/etc/systemd/system/ollama.service.d/override.conf`).
- Uses `sudo tee` for safe file writing (avoids `/tmp` race conditions).
- Falls back to launching `ollama serve` in a subprocess if systemd is unavailable.
- Automatically opens **UFW firewall rules** for port `11434` when binding to LAN.
- Displays the LAN IP address for immediate access confirmation.

### 🖥️ Open WebUI (Docker)
- Launches [Open WebUI](https://github.com/open-webui/open-webui) in a Docker container on port `3000`, bridged to the Ollama backend via `host.docker.internal`.
- Detects if the container already exists and starts it, or performs a fresh pull and run.
- **Stability verification**: waits 15 seconds post-launch, then inspects container state to confirm it's still running.
- On crash detection, automatically fetches and displays the last 15 lines of Docker logs with a likely cause diagnosis (e.g., OOM on low-RAM hardware).
- Opens UFW firewall for port `3000` on success.
- Warns the user that backend initialization can take 1–3 minutes.

### ☁️ Cloudflare WAN Tunnel
- Uses `cloudflared` to create a **zero-config, no-account required** public tunnel via `trycloudflare.com`.
- Lets you choose which service to expose: the raw **Ollama API** (port `11434`) or the **Open WebUI** interface (port `3000`).
- When tunneling the API, automatically **locks Ollama to `127.0.0.1`** first to prevent unauthenticated direct LAN access.
- Streams `cloudflared` stderr line-by-line and extracts only the `trycloudflare.com` URL using a compiled regex — no noise from raw logs.
- Graceful shutdown on `Ctrl+C` with clean process termination.

### 🛑 Service Shutdown
- Stops the Ollama systemd service and kills any lingering `ollama` processes.
- Stops the `open-webui` Docker container.
- Handles both sudo and non-sudo environments automatically.

### 🛫 Pre-flight Dependency Check
- On launch, checks for: `curl`, `ollama`, `docker`, `cloudflared`.
- Offers to **auto-install missing dependencies**:
  - **Ollama**: via official `install.sh`
  - **Docker**: via `get.docker.com`
  - **Cloudflared**: downloads the `.deb` package and installs via `dpkg`
- Prints a color-coded dependency status report before entering the main menu.
- Refuses to proceed without `curl` (hard exit).

### 📊 Live System Stats Dashboard
- Displays **available RAM** (from `/proc/meminfo`) and **free disk space** on every menu refresh.
- Shows the current **LAN IP address**.
- Indicates permission mode: `ROOT CAPABLE` (sudo available) vs `STANDARD USER`.

---

## Requirements

| Dependency | Purpose | Auto-Installable |
|---|---|---|
| Python 3.6+ | Run the script | No |
| `curl` | Dependency installation | No *(hard requirement)* |
| `ollama` | LLM backend & model registry | ✅ Yes |
| `docker` | Open WebUI container runtime | ✅ Yes |
| `cloudflared` | WAN tunneling | ✅ Yes |
| `ufw` *(optional)* | Firewall management | No |
| `sudo` *(optional)* | Systemd & privileged operations | No |

**OS:** Linux (Debian/Ubuntu recommended). Systemd-based distros get the best experience (persistent Ollama network config). Non-systemd environments fall back gracefully.

---

## Installation

```bash
# Clone or download the script
git clone [https://github.com/ashardian/GGUForge.git](https://github.com/ashardian/GGUForge.git)
cd gguf-manager

# Make executable
chmod +x llm2.py

# Run
python3 llm2.py
```

No virtual environment or `pip install` required — the script uses only Python standard library modules (`os`, `subprocess`, `sys`, `shutil`, `socket`, `time`, `re`).

---

## Usage

```bash
python3 llm2.py
```

On first launch, the **pre-flight check** runs automatically. It detects missing dependencies and offers to install them. After that, you land on the main dashboard.

```
=================================================================
 🧠 GGUF Manager & Deployment Dashboard (v13.0 - Diagnostic Edition)
=================================================================
 🖥️  Target IP: 192.168.1.105 | Mode: ROOT CAPABLE
 💾 System:    RAM: 11.4 GB | Disk: 87.3 GB Free
=================================================================

[1] 📦 Scan & Build a .gguf Model
[2] 📋 Manage Installed Models
[3] 🚀 Start Backend API (Port 11434)
[4] 🌐 Start Open WebUI Dashboard (Port 3000)
[5] ☁️  Launch WAN Tunnel (Cloudflare)
[6] 🛑 Stop All Services
[7] ❌ Exit
```

---

## Menu Options

### `[1]` Scan & Build a .gguf Model
1. Optionally include external drives in the scan.
2. Choose to scan home directory or full system root.
3. Select a discovered `.gguf` file from the list.
4. Optionally give it a custom Ollama name, or accept the auto-generated default.
5. The model is built and registered in Ollama's local registry.

### `[2]` Manage Installed Models
- Lists all Ollama-registered models.
- Type a model name to delete it (input is validated before any command runs).

### `[3]` Start Backend API
- Binds Ollama to `0.0.0.0:11434` for LAN access.
- Opens UFW rule if `ufw` is present.
- Prints the accessible LAN URL on success.

### `[4]` Start Open WebUI Dashboard
- Starts Ollama on LAN first, then launches/restarts the Docker container.
- Verifies container is stable 15 seconds after launch.
- Shows crash logs if container exits immediately.

### `[5]` Launch WAN Tunnel
- Choose API (11434) or WebUI (3000) to expose.
- Prints the live `trycloudflare.com` URL when the tunnel is ready.
- Press `Ctrl+C` to terminate cleanly.

### `[6]` Stop All Services
- Stops Ollama (systemd + process kill).
- Stops the Open WebUI Docker container.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    llm2.py (CLI)                     │
│                                                      │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────┐  │
│  │ GGUF Scanner│   │ Ollama Mgmt  │   │  System  │  │
│  │ (filesystem)│   │ (build/list/ │   │  Stats   │  │
│  └──────┬──────┘   │  delete)     │   │ (RAM/IP) │  │
│         │          └──────┬───────┘   └──────────┘  │
│         └────────────────►│                          │
│                     ┌─────▼──────┐                   │
│                     │   Ollama   │◄──systemd override │
│                     │  :11434    │                   │
│                     └─────┬──────┘                   │
│                           │                          │
│              ┌────────────┼────────────┐             │
│              ▼            ▼            ▼             │
│         Open WebUI   Cloudflare    UFW Rules         │
│        (Docker :3000) Tunnel      (auto-manage)      │
└─────────────────────────────────────────────────────┘
```

---

## Configuration

These constants are defined at the top of the script and can be edited directly:

| Variable | Default | Description |
|---|---|---|
| `MODEL_EXTENSION` | `.gguf` | File extension for model discovery |
| `SKIP_DIRS` | `/proc`, `/sys`, `/dev`, etc. | Directories excluded from filesystem scan |
| `EXTERNAL_DRIVE_PATHS` | `/media`, `/mnt`, `/run/media` | Paths searched when external drive scan is enabled |
| `VERSION` | `13.0 - Diagnostic Edition` | Version string shown in the header |

---

## Hugging Face Integration

Open WebUI supports pulling models directly from Hugging Face, but gated models require an access token. You can configure this directly within the script's Docker deployment.

### How to configure your Hugging Face Token:

1. Obtain a **Read Access Token** from your [Hugging Face Settings -> Access Tokens](https://huggingface.co/settings/tokens).
2. Open `llm2.py` in your text editor (e.g., `nano llm2.py`).
3. Scroll down to the `start_open_webui()` function.
4. Locate the Docker command arguments array. Modify the `-e` flags to include your token:

```python
cmd = docker_cmd_base + [
    "run", "-d", 
    "-p", "3000:8080", 
    "--add-host=host.docker.internal:host-gateway",
    "-e", "OLLAMA_BASE_URL=[http://host.docker.internal:11434](http://host.docker.internal:11434)",
    "-e", "HF_ENDPOINT=[https://hf-mirror.com](https://hf-mirror.com)",
    "-e", "HF_TOKEN=hf_your_actual_token_here", # <--- UPDATE THIS LINE
    "-v", "open-webui:/app/backend/data",
    "--name", "open-webui",
    "--restart", "always",
    "ghcr.io/open-webui/open-webui:main"
]
```

5. Save the file. When you launch Open WebUI (Option `[4]`), Docker will securely pass your token, granting the UI access to your gated Hugging Face repositories.

---

## Security Notes

- **Model name validation**: The delete function validates input against `^[a-zA-Z0-9_\-\.:]+$` before passing to `ollama rm` — prevents shell injection.
- **Safe file writes**: Systemd override config is written using `sudo tee` rather than writing to `/tmp` first, avoiding TOCTOU race conditions.
- **Tunnel security**: When exposing the Ollama API via Cloudflare tunnel, the tool automatically rebinds Ollama to `localhost` only, so LAN clients lose direct API access while the tunnel is live.
- **UFW cleanup**: Firewall rules opened for LAN serving can be closed via the Stop Services function.
- **No persistent credentials**: The tool does not store API keys, tokens, or passwords. All operations are ephemeral.

> ⚠️ **Note**: The Cloudflare `trycloudflare.com` tunnel is public and unauthenticated. Anyone with the URL can access your Ollama API or WebUI. Use it only for temporary, controlled access.

---

## Known Limitations

- **Linux only.** macOS and Windows are not supported (relies on `/proc/meminfo`, `systemd`, `pkill`, etc.)
- **No GPU configuration.** GPU acceleration (e.g., CUDA, ROCm) must be configured in Ollama separately.
- **Open WebUI takes 1–3 minutes** to become responsive after Docker starts — this is expected behavior.
- **Cloudflare tunnel URLs are temporary.** Each `cloudflared` session generates a new random URL.
- **Sudo is optional but recommended.** Without it, systemd configuration is skipped and the Ollama fallback subprocess may not persist across reboots.

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `❌ Ollama is missing. Most features will fail` | Ollama not installed | Run option `[1]` pre-flight or install manually: `curl -fsSL https://ollama.com/install.sh \| sh` |
| Open WebUI crashes immediately | OOM (low RAM) or corrupted Docker volume | Stop the Ollama model first; add swap: `sudo fallocate -l 4G /swapfile` |
| `Could not fetch models. Is Ollama running?` | Ollama service not started | Run menu option `[3]` first |
| Tunnel shows no URL | `cloudflared` can't reach the internet | Check network/firewall; ensure port `7844` (UDP) is not blocked |
| `Docker execution failed` | User not in `docker` group | Run `sudo usermod -aG docker $USER` and re-login |
| `❌ 'curl' is missing` | curl not installed | `sudo apt install curl` |
| Port 11434 / 3000 blocked on LAN | UFW rules not applied (no sudo) | Manually run: `sudo ufw allow 11434/tcp && sudo ufw allow 3000/tcp` |

---

## License

MIT License — see `LICENSE` file for details.

---

*Built for the self-hosting community. No cloud. No subscriptions. Your hardware, your models.*
```
