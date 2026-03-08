# aLiGN – Windows Installer

This directory contains everything needed to build a self-contained Windows
installer (`.exe`) for **aLiGN** using [Inno Setup 6](https://jrsoftware.org/isinfo.php).

---

## Quick Start

### For End Users (Install aLiGN)

1. **Download** `aLiGN-Setup.exe`
2. **Run it** and choose where to install
3. **Wait** for services to start (5–15 min on first run)
4. **✓ Dashboard opens automatically**

No other input needed. Services auto-start and you see the app immediately.

---

### For Developers (Build the Installer)

1. **Install** [Inno Setup 6](https://jrsoftware.org/isdl.php)
2. **Open** Command Prompt in repo root
3. **Run:**
   ```cmd
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" aLiGN\installer\setup.iss
   ```
4. **Get:** `aLiGN\installer\output\aLiGN-Setup.exe`

See [BUILD.md](BUILD.md) for detailed instructions.

---

## Prerequisites (for installation)

| Requirement | Status | How to Install |
|-------------|--------|---|
| **Docker Desktop** | Required | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Windows 10+** | Required | Built-in |
| **Internet** | Recommended | For pulling base images on first run |
| **Disk Space** | 5+ GB | For Docker images and database |

**Note:** The installer will remind users to install Docker if they haven't already.

---

## What Gets Installed

```
C:\Program Files\aLiGN\
├── backend/                    FastAPI application (Python)
├── frontend/                   Next.js dashboard (React)
├── docker-compose.yml          Orchestration file
├── .env                        Environment config (auto-created)
├── start.bat                   Launch services shortcut
├── stop.bat                    Stop services shortcut
├── open-browser.bat            Open dashboard shortcut
└── ... (other support files)
```

---

## First Run Experience

1. **Installation completes**
   - Files extracted
   - `.env` auto-created with sensible defaults
   
2. **Services auto-start** (in background)
   - Docker Compose builds images
   - PostgreSQL database starts
   - FastAPI backend boots
   - Next.js frontend compiles
   
3. **Dashboard opens**
   - Browser shows `http://localhost:3000/dashboard`
   - Full working application visible

**Duration:** 5–15 minutes (mostly Docker image build)

---

## After Installation

Users have three convenient shortcuts:

| Shortcut | Action | Location |
|----------|--------|----------|
| **Start aLiGN** | Build & start services | Start Menu + Desktop |
| **Stop aLiGN** | Stop services gracefully | Start Menu |
| **Open aLiGN in Browser** | Open dashboard | Start Menu |

---

## Customization

Edit `setup.iss` before building to customize:

```ini
#define MyAppName        "aLiGN"
#define MyAppVersion     "1.0"
#define MyAppPublisher   "Your Company"
#define MyAppURL         "https://your-support-url"
```

Then rebuild the installer.

See [BUILD.md](BUILD.md) for full customization options.

---

## Troubleshooting

**"Docker Desktop does not appear to be installed"**
- Click YES to open download page
- Install Docker, restart machine
- Rerun installer or `start.bat`

**"Services not running after install"**
- Check: `docker-compose ps`
- View logs: `docker-compose logs backend`
- Verify Docker is actually running (check system tray)

**"Dashboard is blank / doesn't load"**
- Wait 30 seconds (services still initializing)
- Refresh browser (Ctrl+R)
- Check: `docker-compose logs`

---

## File Reference

| File | Purpose |
|------|---------|
| `setup.iss` | Main Inno Setup configuration script |
| `scripts/start.bat` | Starts all services (runs auto on install) |
| `scripts/stop.bat` | Stops services gracefully |
| `scripts/open-browser.bat` | Opens dashboard URL |
| `output/aLiGN-Setup.exe` | Final compiled installer *(created by build)* |
| `BUILD.md` | Developer build guide |
| `README.md` | This file |

---

## Support

- **aLiGN Repository:** [github.com/flencrypto/aLiGN](https://github.com/flencrypto/aLiGN)
- **Docker Help:** [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Inno Setup Docs:** [jrsoftware.org](https://jrsoftware.org/)

---

**Questions or issues?** Open an issue on GitHub or check [BUILD.md](BUILD.md) for detailed troubleshooting.


| Step | Detail |
|------|--------|
| **Prerequisite check** | Detects whether Docker is on `PATH`. Offers to open the Docker Desktop download page if missing. |
| **File copy** | Copies the full project source (excluding `node_modules`, `.next`, `__pycache__`, etc.) to the chosen install directory (default `C:\Program Files\aLiGN`). |
| **Environment setup** | Copies `.env.example` → `.env` if `.env` does not already exist. |
| **Start Menu** | Creates an **aLiGN** folder with shortcuts: *Start aLiGN*, *Stop aLiGN*, *Open in Browser*, *Uninstall*. |
| **Desktop shortcut** | Places an *aLiGN* shortcut on the Desktop that opens `http://localhost:3000`. |
| **Uninstall** | Registered with Windows *Add / Remove Programs*. Stopping containers is attempted automatically before files are removed. |

---

## End-user prerequisites (target machine)

| Requirement | Notes |
|-------------|-------|
| Windows 10 64-bit or later | — |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Must be **running** before launching *Start aLiGN* |

---

## Helper scripts

After installation the following batch scripts live in the install directory:

| Script | Purpose |
|--------|---------|
| `start.bat` | Runs `docker-compose up -d --build` and opens `http://localhost:3000` |
| `stop.bat` | Runs `docker-compose down` |
| `open-browser.bat` | Opens `http://localhost:3000` in the default browser |

---

## Customising the installer

Edit `installer/setup.iss`:

* **`MyAppVersion`** – bump the version string.
* **`DefaultDirName`** – change the default install path.
* **`[Files]`** – add or remove files / directories to bundle.
* **`[Icons]`** – add additional shortcuts.
