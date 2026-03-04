# aLiGN – Windows Installer

This directory contains everything needed to build a self-contained Windows
installer (`.exe`) for **aLiGN** using [Inno Setup 6](https://jrsoftware.org/isinfo.php).

---

## Prerequisites (build machine)

| Tool | Version | Notes |
|------|---------|-------|
| [Inno Setup 6](https://jrsoftware.org/isdl.php) | 6.x | Adds `ISCC.exe` to PATH |
| Windows 10/11 (or CI runner) | — | Required by Inno Setup |

---

## Build the installer locally

1. Install **Inno Setup 6** from <https://jrsoftware.org/isdl.php>.
2. Open a command prompt in the **repository root** (not inside `installer/`).
3. Run:

   ```cmd
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
   ```

   The compiled installer is written to:

   ```
   installer\output\aLiGN-Setup.exe
   ```

Alternatively, open `installer\setup.iss` in the Inno Setup IDE and press **F9**.

---

## CI / automated builds

A GitHub Actions workflow at `.github/workflows/build-installer.yml` automatically
compiles the installer whenever:

* a `v*` tag is pushed (e.g. `git tag v1.0.0 && git push --tags`), or
* the workflow is triggered manually via **Actions → Build Windows Installer → Run workflow**.

The compiled `.exe` is uploaded both as a workflow **artifact** and as a
**GitHub Release asset** (for tagged runs).

---

## What the installer does

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
