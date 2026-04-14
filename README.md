<div align="center">

# 🧠 GGUForge

### GGUF Manager & Deployment Dashboard

*A terminal-based management suite for running, deploying, and exposing local LLMs via Ollama — with an integrated Open WebUI interface and Cloudflare WAN tunneling.*

<br>

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=for-the-badge&logo=linux&logoColor=white)](https://kernel.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-black?style=for-the-badge)](https://ollama.com)
[![Docker](https://img.shields.io/badge/Docker-Required-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

<br>

> **No cloud. No subscriptions. Your hardware, your models.**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Menu Options](#-menu-options)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Hugging Face Integration](#-hugging-face-integration)
- [Security Notes](#-security-notes)
- [Known Limitations](#-known-limitations)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🌐 Overview

**GGUForge** is a single-file Python CLI tool that turns any Linux machine into a fully functional local LLM server — no cloud required.

It automates the entire pipeline:

- 🔍 **Scans** your filesystem for `.gguf` model files
- 📦 **Registers** them with Ollama automatically
- 🖥️ **Launches** a browser-based chat UI via Docker (Open WebUI)
- ☁️ **Optionally exposes** everything to the internet through a zero-config Cloudflare tunnel

Designed for **self-hosters**, **privacy-conscious users**, and **AI hobbyists** who want full control over their models without touching a cloud API.

---

## ✨ Features

<details>
<summary><b>🔍 GGUF Model Scanner</b></summary>
<br>

- Recursively scans your **home directory**, **entire filesystem (`/`)**, or **external drives** (USB/HDD via `/media`, `/mnt`, `/run/media`) for `.gguf` model files
- Safely skips system directories (`/proc`, `/sys`, `/dev`, `/run`, `/tmp`, `/var/lib/docker`, etc.) to avoid hangs or permission errors
- Presents a numbered list of discovered models for easy selection
- Auto-generates a default Ollama registry name from the filename (e.g. `mistral-7b-q4_k_m:community`)
- Allows custom naming before registration
- Writes a temporary `Modelfile` with sensible defaults and cleans it up after use

</details>

<details>
<summary><b>📦 Ollama Model Manager</b></summary>
<br>

- Lists all models currently registered in Ollama (`ollama list`)
- Allows deletion of registered models directly from the dashboard
- Input validation on model names — only safe characters (`a-z`, `0-9`, `-`, `_`, `.`, `:`) accepted to prevent command injection

</details>

<details>
<summary><b>🚀 Backend API Server (Port 11434)</b></summary>
<br>

- Configures Ollama to bind on `0.0.0.0` (LAN-accessible) via a **systemd override**
- Uses `sudo tee` for safe file writing (avoids `/tmp` race conditions)
- Falls back to launching `ollama serve` in a subprocess if systemd is unavailable
- Automatically opens **UFW firewall rules** for port `11434` when binding to LAN
- Displays the LAN IP address for immediate access confirmation

</details>

<details>
<summary><b>🖥️ Open WebUI (Docker)</b></summary>
<br>

- Launches [Open WebUI](https://github.com/open-webui/open-webui) in a Docker container on port `3000`, bridged to the Ollama backend via `host.docker.internal`
- Detects if the container already exists and starts it, or performs a fresh pull and run
- **Stability verification**: waits 15 seconds post-launch, then inspects container state to confirm it's still running
- On crash detection, automatically fetches and displays the last 15 lines of Docker logs with a likely cause diagnosis
- Opens UFW firewall for port `3000` on success

</details>

<details>
<summary><b>☁️ Cloudflare WAN Tunnel</b></summary>
<br>

- Uses `cloudflared` to create a **zero-config, no-account required** public tunnel via `trycloudflare.com`
- Choose which service to expose: the raw **Ollama API** (port `11434`) or the **Open WebUI** interface (port `3000`)
- When tunneling the API, automatically **locks Ollama to `127.0.0.1`** first to prevent unauthenticated direct LAN access
- Streams `cloudflared` stderr line-by-line and extracts only the `trycloudflare.com` URL using a compiled regex
- Graceful shutdown on `Ctrl+C` with clean process termination

</details>

<details>
<summary><b>🛑 Service Shutdown & 📊 Live System Stats</b></summary>
<br>

**Service Shutdown:**
- Stops the Ollama systemd service and kills any lingering `ollama` processes
- Stops the `open-webui` Docker container
- Handles both sudo and non-sudo environments automatically

**Live System Stats Dashboard:**
- Displays **available RAM** (from `/proc/meminfo`) and **free disk space** on every menu refresh
- Shows the current **LAN IP address**
- Indicates permission mode: `ROOT CAPABLE` vs `STANDARD USER`

</details>

<details>
<summary><b>🛫 Pre-flight Dependency Check</b></summary>
<br>

On launch, checks for: `curl`, `ollama`, `docker`, `cloudflared` — and offers to auto-install missing ones:

| Dependency | Install Method |
|---|---|
| Ollama | Official `install.sh` |
| Docker | `get.docker.com` |
| Cloudflared | Downloads `.deb` + installs via `dpkg` |

Prints a color-coded dependency status report before entering the main menu. Refuses to proceed without `curl` (hard exit).

</details>

---

## 📦 Requirements

| Dependency | Purpose | Auto-Installable |
|---|---|:---:|
| Python 3.6+ | Run the script | ❌ |
| `curl` | Dependency installation | ❌ *(hard requirement)* |
| `ollama` | LLM backend & model registry | ✅ |
| `docker` | Open WebUI container runtime | ✅ |
| `cloudflared` | WAN tunneling | ✅ |
| `ufw` *(optional)* | Firewall management | ❌ |
| `sudo` *(optional)* | Systemd & privileged operations | ❌ |

> **OS:** Linux (Debian/Ubuntu recommended). Systemd-based distros get the best experience. Non-systemd environments fall back gracefully.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/ashardian/GGUForge.git
cd GGUForge

# Make executable
chmod +x gguforge.py

# Run
python3 gguforge.py
```

> **No virtual environment or `pip install` required.** The script uses only Python standard library modules: `os`, `subprocess`, `sys`, `shutil`, `socket`, `time`, `re`.

---

## 🖥️ Usage

```bash
python3 gguforge.py
```

On first launch, the **pre-flight check** runs automatically, detects missing dependencies, and offers to install them. After that, you land on the main dashboard:

```
=================================================================
 🧠 GGUF Manager & Deployment Dashboard (v13.0 - Diagnostic Edition)
=================================================================
 🖥️  Target IP: 192.168.1.105 | Mode: ROOT CAPABLE
 💾 System:    RAM: 11.4 GB  | Disk: 87.3 GB Free
=================================================================

[1] 📦 Scan & Build a .gguf Model
[2] 📋 Manage Installed Models
[3] 🚀 Start Backend API (Port 11434)
[4] 🌐 Start Open WebUI Dashboard (Port 3000)
[5] ☁️  Launch WAN Tunnel (Cloudflare)
[6] 🛑 Stop All Services
[7] ❌ Exit

=================================================================
Select an option:
```

---

## 📖 Menu Options

### `[1]` Scan & Build a .gguf Model
1. Optionally include external drives in the scan
2. Choose to scan home directory or full system root
3. Select a discovered `.gguf` file from the numbered list
4. Optionally give it a custom Ollama name, or accept the auto-generated default
5. The model is built and registered in Ollama's local registry

### `[2]` Manage Installed Models
- Lists all Ollama-registered models
- Type a model name to delete it (input is validated before any command runs)

### `[3]` Start Backend API
- Binds Ollama to `0.0.0.0:11434` for LAN access
- Opens UFW rule if `ufw` is present
- Prints the accessible LAN URL on success

### `[4]` Start Open WebUI Dashboard
- Starts Ollama on LAN first, then launches/restarts the Docker container
- Verifies container stability 15 seconds after launch
- Shows crash logs if container exits immediately

### `[5]` Launch WAN Tunnel
- Choose to expose the API (port `11434`) or WebUI (port `3000`)
- Prints the live `trycloudflare.com` URL when the tunnel is ready
- Press `Ctrl+C` to terminate cleanly

### `[6]` Stop All Services
- Stops Ollama (systemd + process kill)
- Stops the Open WebUI Docker container

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     gguforge.py  (CLI)                  │
│                                                         │
│  ┌─────────────┐   ┌───────────────┐   ┌────────────┐   │
│  │ GGUF Scanner│   │  Ollama Mgmt  │   │   System   │   │
│  │ (filesystem)│   │ (build/list/  │   │   Stats    │   │
│  └──────┬──────┘   │   delete)     │   │ (RAM / IP) │   │
│         │          └──────┬────────┘   └────────────┘   │
│         └────────────────►│                             │
│                    ┌──────▼──────┐                      │
│                    │   Ollama    │◄── systemd override  │
│                    │   :11434    │                      │
│                    └──────┬──────┘                      │
│                           │                             │
│             ┌─────────────┼─────────────┐               │
│             ▼             ▼             ▼               │
│        Open WebUI    Cloudflare      UFW Rules          │
│       (Docker :3000)  Tunnel       (auto-manage)        │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

These constants are defined at the top of the script and can be edited directly:

| Variable | Default | Description |
|---|---|---|
| `MODEL_EXTENSION` | `.gguf` | File extension for model discovery |
| `SKIP_DIRS` | `/proc`, `/sys`, `/dev`, etc. | Directories excluded from filesystem scan |
| `EXTERNAL_DRIVE_PATHS` | `/media`, `/mnt`, `/run/media` | Paths searched when external drive scan is enabled |
| `VERSION` | `13.0 - Diagnostic Edition` | Version string shown in the header |

---

## 🤗 Hugging Face Integration

Open WebUI supports pulling models directly from Hugging Face. Gated models require an access token, which you can configure in the script.

**Steps:**

1. Get a **Read Access Token** from [Hugging Face Settings → Access Tokens](https://huggingface.co/settings/tokens)
2. Open `gguforge.py` and navigate to the `start_open_webui()` function
3. Update the Docker command to include your token:

```python
cmd = docker_cmd_base + [
    "run", "-d",
    "-p", "3000:8080",
    "--add-host=host.docker.internal:host-gateway",
    "-e", "OLLAMA_BASE_URL=http://host.docker.internal:11434",
    "-e", "HF_ENDPOINT=https://hf-mirror.com",
    "-e", "HF_TOKEN=hf_your_actual_token_here",   # <-- UPDATE THIS
    "-v", "open-webui:/app/backend/data",
    "--name", "open-webui",
    "--restart", "always",
    "ghcr.io/open-webui/open-webui:main"
]
```

4. Save the file. The next time you launch Open WebUI (Option `[4]`), Docker will securely pass your token.

---

## 🔒 Security Notes

| Concern | Mitigation |
|---|---|
| **Command injection** | Model name input validated against `^[a-zA-Z0-9_\-\.:]+$` before passing to `ollama rm` |
| **Race conditions** | Systemd override written using `sudo tee` instead of `/tmp` (avoids TOCTOU) |
| **Unauthenticated LAN exposure** | When tunneling the API, Ollama is automatically rebound to `localhost` only |
| **Firewall cleanup** | UFW rules opened for LAN serving can be closed via Stop Services |
| **No credential storage** | The tool stores no API keys, tokens, or passwords — all operations are ephemeral |

> ⚠️ **Warning:** The `trycloudflare.com` tunnel is **public and unauthenticated**. Anyone with the URL can access your Ollama API or WebUI. Use it only for temporary, controlled access sessions.

---

## ⚠️ Known Limitations

- **Linux only** — macOS and Windows are not supported (relies on `/proc/meminfo`, `systemd`, `pkill`, etc.)
- **No GPU configuration** — GPU acceleration (CUDA, ROCm) must be configured in Ollama separately
- **Open WebUI takes 1–3 minutes** to become responsive after Docker starts — this is expected
- **Cloudflare tunnel URLs are temporary** — each `cloudflared` session generates a new random URL
- **Sudo is optional but recommended** — without it, systemd config is skipped and Ollama may not persist across reboots

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `❌ Ollama is missing` | Ollama not installed | Run pre-flight or: `curl -fsSL https://ollama.com/install.sh \| sh` |
| Open WebUI crashes immediately | OOM (low RAM) or corrupted Docker volume | Stop model first; add swap: `sudo fallocate -l 4G /swapfile` |
| `Could not fetch models. Is Ollama running?` | Ollama service not started | Run menu option `[3]` first |
| Tunnel shows no URL | `cloudflared` can't reach the internet | Check firewall; ensure port `7844` (UDP) is not blocked |
| `Docker execution failed` | User not in `docker` group | `sudo usermod -aG docker $USER` then re-login |
| `❌ 'curl' is missing` | curl not installed | `sudo apt install curl` |
| Port 11434 / 3000 blocked on LAN | UFW rules not applied (no sudo) | `sudo ufw allow 11434/tcp && sudo ufw allow 3000/tcp` |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

*Built for the self-hosting community.*
*No cloud. No subscriptions. Your hardware, your models.*

<br>

⭐ **If you find this useful, consider starring the repo!** ⭐

</div>
