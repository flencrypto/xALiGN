# Installing aLiGN Locally on Windows

This guide covers three ways to run aLiGN on a Windows machine.

| Method | Best for |
|--------|----------|
| [A – Windows Installer (.exe)](#option-a--windows-installer-exe) | Non-developers; one-click setup |
| [B – Docker Compose (manual)](#option-b--docker-compose-manual) | Developers who prefer Docker |
| [C – Manual (no Docker)](#option-c--manual-installation-no-docker) | Developers who want full control of each service |

---

## Prerequisites

### Option A – Windows Installer
- Windows 10 64-bit or later
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) installed and **running**

### Options B & C
- Windows 10 64-bit or later
- [Git for Windows](https://git-scm.com/download/win) (includes Git Bash)
- Option B only: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- Option C only:
  - [Node.js 20+](https://nodejs.org/) (LTS recommended)
  - [Python 3.11+](https://www.python.org/downloads/windows/) — tick **"Add Python to PATH"** during installation

---

## Option A – Windows Installer (.exe)

This is the easiest path. A pre-built installer bundles everything and wires up Start Menu shortcuts for you.

### 1 — Download the installer

Go to the [Releases page](https://github.com/flencrypto/aLiGN/releases) and download the latest `aLiGN-Setup.exe`.

### 2 — Run the installer

Double-click `aLiGN-Setup.exe` and follow the wizard:

1. **Welcome screen** – click **Next**.
2. **Docker check** – if Docker Desktop is not detected you will be prompted to download it. Install Docker Desktop, start it, then re-run the installer.
3. **Installation folder** – the default is `C:\Program Files\aLiGN`. Change it if you prefer.
4. **Install** – click **Install** and wait for the files to be copied.
5. **Finish** – optionally tick *Open aLiGN in browser now* (services must be started first).

### 3 — Start aLiGN

Open the **aLiGN** folder in the Start Menu and click **Start aLiGN**.

A console window will open, build and start the Docker containers, then automatically open `http://localhost:3000` in your browser.

| URL | What it is |
|-----|-----------|
| `http://localhost:3000` | aLiGN frontend |
| `http://localhost:8000/docs` | Backend API (Swagger UI) |

### 4 — Stop aLiGN

Use **Stop aLiGN** from the Start Menu (or the `stop.bat` in the install folder).

### Uninstall

Go to **Settings → Apps** (or *Add / Remove Programs*), search for **aLiGN**, and click **Uninstall**. Running containers are stopped automatically before files are removed.

---

## Option B – Docker Compose (manual)

### 1 — Prerequisites

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) installed and running
- [Git for Windows](https://git-scm.com/download/win)

Verify Docker is working by opening **PowerShell** or **Command Prompt** and running:

```powershell
docker --version
```

Then check which Compose command is available on your system:

```powershell
# Try the newer built-in plugin first:
docker compose version

# If the above is not recognised, try the legacy standalone binary:
docker-compose --version
```

Use whichever command prints a version number — that is the one to use in the steps below.

### 2 — Clone the repository

```powershell
git clone https://github.com/flencrypto/aLiGN.git
cd aLiGN
```

### 3 — Create the environment file

```powershell
copy .env.example .env
```

Open `.env` in a text editor and adjust any values you need (API keys, etc.). The defaults work for a local development setup.

### 4 — Build and start the services

```powershell
docker compose up --build
```

The first run downloads base images and installs dependencies — this can take several minutes. Subsequent starts are much faster.

Once you see output similar to:

```
frontend  | ▲ Next.js 15.x.x
frontend  | - Local: http://localhost:3000
backend   | INFO:     Uvicorn running on http://0.0.0.0:8000
```

the application is ready.

| URL | What it is |
|-----|-----------|
| `http://localhost:3000` | aLiGN frontend |
| `http://localhost:8000/docs` | Backend API (Swagger UI) |

### 5 — Stop the services

Press `Ctrl+C` in the terminal window, then run:

```powershell
docker compose down
```

### Running in the background (detached mode)

```powershell
docker compose up -d --build
```

To stop:

```powershell
docker compose down
```

---

## Option C – Manual Installation (no Docker)

Use this method if you cannot use Docker or want to run each service directly on your machine.

### 1 — Prerequisites

Install the following before starting:

| Tool | Download | Notes |
|------|----------|-------|
| Git for Windows | https://git-scm.com/download/win | Includes Git Bash |
| Node.js 20+ (LTS) | https://nodejs.org/ | Tick the option to add to PATH |
| Python 3.11+ | https://www.python.org/downloads/windows/ | **Tick "Add Python to PATH"** |

Open **PowerShell** and verify:

```powershell
git --version
node --version
python --version
```

### 2 — Clone the repository

```powershell
git clone https://github.com/flencrypto/aLiGN.git
cd aLiGN
```

### 3 — Configure the environment

```powershell
copy .env.example .env
```

Open `.env` and set at minimum:

```env
DATABASE_URL=sqlite:///./align.db
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
CORS_ORIGINS=http://localhost:3000
```

### 4 — Set up the backend

Open a **PowerShell** window in the repository root:

```powershell
cd backend

# Create a virtual environment
python -m venv .venv

# Activate it (PowerShell)
.\.venv\Scripts\Activate.ps1
```

> **Tip – ExecutionPolicy error?** If PowerShell blocks the script, run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> Then re-run `.\.venv\Scripts\Activate.ps1`. Alternatively, use **Command Prompt** instead and run `.venv\Scripts\activate.bat`.

```powershell
# Install dependencies
pip install -r requirements.txt

# Return to the repository root and start the backend API server
cd ..
uvicorn backend.main:app --reload --port 8000
```

> **Tip:** If you see `python` not found, try `py -3` instead of `python`.

Leave this terminal window open. The backend is running at `http://localhost:8000`.

### 5 — Set up the frontend

Open a **second PowerShell** window in the repository root:

```powershell
cd frontend

# Copy the environment file for the frontend (including any changes you just made)
copy ..\.env .env.local
```

Open `frontend\.env.local` and make sure this line is present (it should already be set):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Then install dependencies and start the development server:

```powershell
npm install
npm run dev
```

Once you see:

```
▲ Next.js 15.x.x
- Local: http://localhost:3000
```

the frontend is ready.

| URL | What it is |
|-----|-----------|
| `http://localhost:3000` | aLiGN frontend |
| `http://localhost:8000/docs` | Backend API (Swagger UI) |

### 6 — Stop the services

- **Backend:** press `Ctrl+C` in the backend terminal and run `deactivate` to exit the virtual environment.
- **Frontend:** press `Ctrl+C` in the frontend terminal.

---

## Troubleshooting

### Docker Desktop: "WSL 2 installation is incomplete"

Docker Desktop on Windows uses WSL 2 by default. If prompted, follow the link in the error message to install the WSL 2 Linux kernel update, restart your machine, then start Docker Desktop again.

### Python: `python` command not found

- Ensure you ticked **"Add Python to PATH"** during installation.
- Alternatively use `py -3` instead of `python` (the Python Launcher for Windows).
- You can also add Python to PATH manually: **Settings → System → About → Advanced system settings → Environment Variables**.

### Node.js: `npm install` fails with EACCES / permission errors

Run PowerShell **as Administrator**, or change the npm global prefix to a directory you own:

```powershell
npm config set prefix "$env:APPDATA\npm"
```

### Port already in use

If another process is already using port `3000` or `8000`, either stop that process or change the ports:

- **Backend port:** pass `--port <number>` to `uvicorn`, and update `NEXT_PUBLIC_API_URL` in `.env` / `.env.local` to point to the new backend URL.
- **Frontend port:** run `npm run dev -- -p <number>`. If you change the frontend port, also update the hard-coded allowed origin in `backend/main.py` (look for `allow_origins=["http://localhost:3000"]`) to match your new frontend URL (for example, `http://localhost:<number>`).

### "docker compose" vs "docker-compose"

Newer versions of Docker Desktop ship `docker compose` (no hyphen) as a built-in plugin, while older installations use a separate `docker-compose` binary. Use whichever command is available on your system; if `docker compose` is not recognized, try `docker-compose`, and vice versa.

---

## Next steps

- Edit `.env` to add optional API keys (xAI/Grok, OpenAI, Anthropic) for AI-assisted features.
- See the [API overview](../README.md#-api-overview) for the full list of REST endpoints.
- See the [Architecture section](../README.md#️-architecture) for a map of the codebase.
