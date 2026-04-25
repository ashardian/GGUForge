<div align="center">

# 🧠 GGUForge

### GGUF Model Manager & Local AI Deployment Dashboard for Linux

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=flat-square&logo=linux)](https://kernel.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-14.0-purple?style=flat-square)]()
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-black?style=flat-square)](https://ollama.com)

**Deploy, manage, and expose local AI models — entirely from your terminal.**

GGUForge is a headless-friendly Python dashboard for Linux that automates the full lifecycle of local LLM deployment: scanning your filesystem for GGUF models, registering them with Ollama, launching Open WebUI via Docker, and tunneling them to the internet through Cloudflare — all from a single terminal interface with no GUI required.

</div>

---

## 📋 Table of Contents

- [Why GGUForge](#-why-gguforge)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Dashboard Menu](#-dashboard-menu)
- [Feature Walkthrough](#-feature-walkthrough)
- [HuggingFace Token](#-huggingface-token)
- [Data Directory](#-data-directory)
- [File Structure](#-file-structure)
- [Tested On](#-tested-on)
- [Changelog](#-changelog)
- [License](#-license)

---

## 🎯 Why GGUForge

Most local AI tools assume a desktop GUI. GGUForge is built for Linux users who work over SSH, run headless servers, or just prefer the terminal. It bridges the gap between raw GGUF files on disk and a fully functional, network-accessible AI deployment stack — without touching a browser or clicking anything.

| Capability | LM Studio | Ollama CLI | **GGUForge** |
|---|:---:|:---:|:---:|
| Headless / SSH operation | ❌ | ✅ | ✅ |
| Auto GGUF filesystem scan | ❌ | ❌ | ✅ |
| Open WebUI deployment | ❌ | ❌ | ✅ |
| Cloudflare WAN tunnel | ❌ | ❌ | ✅ |
| LAN API exposure via systemd | ❌ | Manual | ✅ |
| Persistent logging | ❌ | ❌ | ✅ |
| HF token management | ✅ | ❌ | ✅ |
| Single unified dashboard | ❌ | ❌ | ✅ |

---

## ✨ Features

- **🔍 GGUF Filesystem Scanner** — recursively searches your home directory, external drives, or the entire filesystem for `.gguf` files. Displays each model's name and file size before you select it so you know what you are loading.

- **📦 GGUF → Ollama Registration** — builds a proper `Modelfile` with custom model name, temperature, and system prompt, then registers it into Ollama's local registry in one step.

- **⬇️ Pull by Name** — download any model directly from the [Ollama model library](https://ollama.com/library) without leaving the dashboard (e.g. `llama3`, `mistral`, `qwen2.5:3b`).

- **📋 Model Manager** — list all installed Ollama models with sizes, and delete them with a confirmation prompt to prevent accidents.

- **🔍 Ollama API Status** — live health check against the Ollama REST API with a full listing of registered models and their sizes.

- **🚀 Ollama LAN Exposure** — writes a `systemd` override to bind Ollama to `0.0.0.0`, reloads the daemon, opens the UFW firewall rule, and polls the API until it is confirmed live — no fixed sleep timers.

- **🌐 Open WebUI (Docker)** — pulls a pinned Docker image, injects the correct environment variables (Ollama base URL, RAG engine, HF token, stable secret key), and starts the container with `--restart always`. Includes crash diagnostics with log output if the container exits immediately.

- **📋 Live WebUI Logs** — stream Open WebUI container logs in real time directly from the dashboard. Press `Ctrl+C` to return to the menu.

- **🔄 Reset Open WebUI** — safely wipes the container and data volume (type `RESET` to confirm) for a clean slate when accounts get corrupted. Your Ollama models and HF token are untouched.

- **☁️ Cloudflare WAN Tunnel** — launches a `cloudflared` quick-tunnel to expose either the Ollama API or the Open WebUI interface over a public HTTPS URL. The URL is extracted automatically from the process output and saved to `~/.gguforge/last_tunnel_url` for reference after the session ends.

- **🛑 Stop All Services** — gracefully stops Ollama (systemd + pkill fallback) and the Open WebUI container, and closes the corresponding UFW firewall rules.

- **🔑 HuggingFace Token Manager** — save, live-validate against the HF API, view (masked with permission check), and delete your HF access token from inside the dashboard. Stored at `~/.gguforge/hf_token` with `chmod 600` and injected into Docker automatically on every WebUI launch.

- **📄 Persistent Logging** — every significant event (service starts/stops, model registrations, errors, tunnel URLs) is written to `~/.gguforge/logs/gguforge.log` with timestamps. View the last 40 entries from the dashboard.

- **🛫 Pre-Flight Check** — on first run, checks for `curl`, `ollama`, `docker`, and `cloudflared`. Offers to install any that are missing using their official install scripts.

---

## 📦 Requirements

| Dependency | Required | Notes |
|---|:---:|---|
| Python 3.10+ | ✅ | Must be installed manually |
| `curl` | ✅ | Used by the auto-installers |
| Ollama | ⚡ | Auto-installable via dashboard |
| Docker | ⚡ | Auto-installable via dashboard (needed for Open WebUI) |
| Cloudflared | ⚡ | Auto-installable via dashboard (needed for WAN tunnel) |
| UFW | ➖ | Optional — firewall rules skipped silently if not present |

> ⚡ = optional but offered for auto-install on first run

**Recommended distros:** Debian 12/13, Ubuntu 22.04/24.04, Linux Mint 21+

---

## 📥 Installation

```bash
# Clone the repository
git clone https://github.com/ashardian/GGUForge.git
cd GGUForge

# No pip install needed — pure Python standard library
python3 main.py
```

On first launch the pre-flight check runs automatically and offers to install any missing dependencies.

---

## 🚀 Quick Start

```bash
python3 main.py
```

**Typical first-run flow:**

1. Pre-flight check runs → installs Ollama + Docker if missing
2. Select **[5]** → Start Ollama Backend API (binds to LAN)
3. Select **[1]** → Scan filesystem and register a GGUF model
4. Select **[6]** → Launch Open WebUI (Docker)
5. On the WebUI page → click **Sign Up** to create your admin account *(first time only)*
6. Select **[8]** → Launch Cloudflare tunnel to share access externally

---

## 🗂️ Dashboard Menu

```
=====================================================================
  🧠  GGUForge — GGUF Manager & Deployment Dashboard  v14.0
=====================================================================
  🖥️  IP:  192.168.1.100  │  Mode: ROOT CAPABLE
  💾 RAM: 3.2/15.5 GB    │  Disk: 142.3 GB Free  │  CPU: 8 cores
=====================================================================

  [ 1] 📦  Scan Filesystem & Register .gguf Model
  [ 2] ⬇️   Pull Model by Name (Ollama Registry)
  [ 3] 📋  Manage / Delete Installed Models
  [ 4] 🔍  Ollama API Status & Model List
  [ 5] 🚀  Start Ollama Backend API       (Port 11434)
  [ 6] 🌐  Start Open WebUI Dashboard     (Port 3000)
  [ 7] 📋  View Open WebUI Live Logs
  [ 8] ☁️   Launch WAN Tunnel (Cloudflare)
  [ 9] 🛑  Stop All Services
  [10] 🔄  Reset Open WebUI  (wipe container + accounts)
  [11] 🔑  Manage HuggingFace Token
  [12] 📄  View Log File
  [ 0] ❌  Exit
```

---

## 🔧 Feature Walkthrough

### Registering a GGUF Model (Option 1)

GGUForge scans your filesystem and lists every `.gguf` file with its size on disk. Select one, assign it a name in the Ollama registry, set temperature and system prompt, and the tool builds and registers the `Modelfile` automatically.

```
--- Found Models (3) ---
  [1] mistral-7b-instruct-v0.2.Q4_K_M.gguf   4.1 GB
       /home/mrx/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf

  [2] qwen2.5-3b-instruct-q8_0.gguf           3.3 GB
       /media/usb/models/qwen2.5-3b-instruct-q8_0.gguf

  [3] gemma-3-4b-it-q4_k_m.gguf               2.6 GB
       /home/mrx/models/gemma-3-4b-it-q4_k_m.gguf
```

### Open WebUI — First Run Notice

> ⚠️ **On the very first launch of Open WebUI, you MUST click Sign Up — not Sign In.**
> No accounts exist yet on a fresh container. GGUForge displays a prominent warning
> banner the first time it creates the container. After creating your admin account,
> all future sessions use Sign In normally.

### Stable Secret Key

GGUForge generates a 64-character `WEBUI_SECRET_KEY` on first use, saves it to `~/.gguforge/webui_secret_key` (chmod 600), and injects it into Docker on every launch. This means your account passwords and sessions survive container rebuilds — a common cause of "wrong password" errors in vanilla Open WebUI setups.

### Cloudflare WAN Tunnel (Option 8)

Exposes either the Ollama API (port 11434) or the Open WebUI interface (port 3000) over a public HTTPS URL with zero configuration.

```
============================================================
  ✅ Tunnel is LIVE!
============================================================

  🌐 Public URL: https://random-name.trycloudflare.com

  📋 URL saved to: /home/mrx/.gguforge/last_tunnel_url
============================================================
```

> **Security note:** Quick tunnels are unauthenticated. Only expose the Ollama API
> in trusted contexts. For production use, add Cloudflare Access in front of the tunnel.

### Resetting Open WebUI (Option 10)

If the account database gets corrupted or you want a clean start, Option 10 wipes the container and volume after you type `RESET` to confirm. Your Ollama models, HF token, and secret key are all preserved — only the WebUI account database is removed.

---

## 🔑 HuggingFace Token

A HuggingFace token is required to access gated models such as Llama 3, Gemma, Mistral Nemo, and others. GGUForge includes a built-in token manager (Option 11) with four operations:

| Sub-option | What it does |
|---|---|
| Save / Update | Paste token → live API validation → shows account name → saves with chmod 600 |
| Test | Hits the HuggingFace API with the saved token and confirms it is still valid |
| Show info | Displays masked token, file path, and permission check (warns if not 600) |
| Delete | Removes the token file with a confirmation prompt |

**Get your token:**
1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **New token** → Role: **Read**
3. Copy the token (starts with `hf_`)
4. Open GGUForge → Option 11 → Save / Update token

**Manual save (if you prefer the terminal):**

```bash
echo "hf_yourtoken" > ~/.gguforge/hf_token
chmod 600 ~/.gguforge/hf_token
```

The token is automatically injected into the Open WebUI Docker container on every launch. After saving or updating a token, restart Open WebUI (Option 6) to apply it.

---

## 📁 Data Directory

GGUForge stores all persistent data under `~/.gguforge/` — nothing is written to system directories.

```
~/.gguforge/
├── hf_token              # HuggingFace API token (chmod 600)
├── webui_secret_key      # Stable WEBUI_SECRET_KEY for Open WebUI (chmod 600)
├── webui_first_run_done  # Flag file — suppresses Sign Up reminder after first launch
├── last_tunnel_url       # Last active Cloudflare tunnel URL
└── logs/
    └── gguforge.log      # Full timestamped event log
```

---

## 🗃️ File Structure

```
gguforge/
├── main.py            # Entry point & dashboard menu (Options 0–12)
├── config.py          # All constants: ports, image tags, paths, filesystem skip dirs
├── ui.py              # Terminal color codes and formatted print helpers
├── logger.py          # Persistent file logger → ~/.gguforge/logs/gguforge.log
├── system.py          # Binary detection, sudo check, LAN IP, RAM/disk/CPU stats
├── firewall.py        # UFW port open/close helpers
├── deps.py            # Pre-flight dependency checks and official auto-installers
├── scanner.py         # Recursive .gguf filesystem scanner with file size display
├── ollama_manager.py  # Ollama: network config, register GGUF, pull, list, delete, status
├── webui.py           # Open WebUI: Docker lifecycle, secret key, first-run, reset, log tail
├── tunnel.py          # Cloudflare quick-tunnel: URL extraction and persistent save
├── services.py        # Graceful stop for all services + UFW firewall cleanup
└── hf_token.py        # HuggingFace token: save, live-validate, view, delete
```

---

## 🖥️ Tested On

| OS | Version | Status |
|---|---|:---:|
| Debian | 13 Trixie (bare metal) | ✅ Verified |
| Linux Mint | 21.x Cinnamon | ✅ Verified |
| Ubuntu | 22.04 / 24.04 LTS | ✅ Verified |

---

## 📝 Changelog

### v14.0 — Multi-Module Edition

| Area | Change |
|---|---|
| **Architecture** | Refactored from a single 463-line monolith into 12 focused modules |
| **Logging** | All events persisted to `~/.gguforge/logs/gguforge.log` with timestamps |
| **Docker image** | Pinned to a specific version tag — was `:main` (unpinned, silently breakable) |
| **RAG fix** | `RAG_EMBEDDING_ENGINE=ollama` injected by default — eliminates HuggingFace 500 error on Open WebUI startup |
| **Stable secret key** | `WEBUI_SECRET_KEY` generated once and reused — accounts and sessions survive container rebuilds |
| **First-run notice** | Prominent warning banner on first container creation: click Sign Up, not Sign In |
| **WebUI reset** | Option 10 — wipe container + volume with typed `RESET` confirmation; preserves models and credentials |
| **HF token manager** | Full dashboard UI: save with live API validation, test validity, view masked + permissions, delete |
| **Startup polling** | `time.sleep()` replaced with real REST API polling — Ollama readiness actually verified before proceeding |
| **Pull by name** | Option 2 — pull models from Ollama registry by name without leaving the dashboard |
| **Model size display** | GGUF scanner shows file size next to every result before selection |
| **Ollama status** | Option 4 — live API health check with registered model listing and sizes |
| **WebUI logs** | Option 7 — real-time container log tail, `Ctrl+C` to return to menu |
| **Tunnel URL save** | Last Cloudflare URL written to `~/.gguforge/last_tunnel_url` after session ends |
| **Delete confirmation** | Model deletion requires explicit `y/N` before proceeding |
| **Firewall cleanup** | Stop All Services now closes the UFW rules it previously opened |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for full terms.

---

<div align="center">

Built for Linux. Runs anywhere Ollama runs.

**[⭐ Star this repo](https://github.com/ashardian/GGUForge)** if GGUForge saved you time.

</div>
