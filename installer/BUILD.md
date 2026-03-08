# Building the aLiGN Windows Installer (.exe)

This guide explains how to build a fully executable, self-installing Windows package for aLiGN.

---

## What You Get

Once built, users will:
1. **Download** `aLiGN-Setup.exe`
2. **Run it** and choose an installation folder
3. **Wait** for Docker Compose to build and start services (5-15 minutes on first run)
4. **See** the dashboard open automatically in their browser

**No additional input required beyond selecting the installation directory.**

---

## Prerequisites (Your Build Machine)

You need these tools installed:

| Tool | Version | Download |
|------|---------|----------|
| **Inno Setup 6** | 6.x or later | [jrsoftware.org](https://jrsoftware.org/isdl.php) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/download/win) |
| **Windows** | 10 or 11 | Built-in |

**Notes:**
- Inno Setup must be installed (it adds `ISCC.exe` to your PATH).
- No need to pre-install Docker or build the images—that happens on the user's machine.
- Everything else (Docker, Node.js, Python) is handled at runtime by the installer.

---

## Step-by-Step Build

### Option 1: Command Line (Recommended)

1. Open **Command Prompt** or **PowerShell** in the **repository root**:
   ```cmd
   cd g:\Apps\xALiGN
   ```

2. Compile the installer:
   ```cmd
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" aLiGN\installer\setup.iss
   ```

3. The compiled `.exe` will be created at:
   ```
   aLiGN\installer\output\aLiGN-Setup.exe
   ```

### Option 2: Inno Setup IDE

1. Open **Inno Setup 6** IDE (search in Windows Start Menu)
2. Open the file: `aLiGN\installer\setup.iss`
3. Press **F9** to compile
4. The `.exe` is output to `aLiGN\installer\output\aLiGN-Setup.exe`

---

## Customization (Before Build)

Edit `aLiGN\installer\setup.iss` to customize:

```ini
#define MyAppName        "aLiGN"          ; Application name
#define MyAppVersion     "1.0"            ; Version number
#define MyAppPublisher   "aLiGN"          ; Publisher name
#define MyAppURL         "https://..."    ; Support URL
```

**Example:** Change version to `1.1`, publisher to `My Company`:
```ini
#define MyAppVersion     "1.1"
#define MyAppPublisher   "My Company"
```

---

## Installation Behavior

When users run `aLiGN-Setup.exe`:

### Pre-Installation
- **Docker Check:** Installer verifies Docker Desktop is installed.
  - If **found**: Proceeds normally.
  - If **missing**: Offers to open the Docker download page.
    - User can install Docker now or later.
    - Installation continues either way.

### Installation Steps
1. User selects installation folder (default: `C:\Program Files\aLiGN`)
2. Files are extracted:
   - Backend (Python FastAPI)
   - Frontend (Next.js React)
   - Docker Compose file
   - Helper scripts
3. `.env` file is created from `.env.example`
4. **Services auto-start** → `start.bat` runs in background
5. **Browser opens** → Dashboard displays at `http://localhost:3000/dashboard`

### First Run (Auto-Startup)
On first run, the `start.bat` script:
- ✓ Checks Docker is running (auto-launches if not)
- ✓ Builds Docker images from Dockerfiles (5-15 min)
- ✓ Creates database and initializes schema
- ✓ Starts all services (backend, frontend, database)
- ✓ Waits for health endpoint
- ✓ Opens dashboard in browser

**Duration:** 5-15 minutes depending on machine spec.

### After Installation
Users have three shortcuts in the Start Menu:
- **Start aLiGN** — Builds and starts services
- **Stop aLiGN** — Stops services (data preserved)
- **Open aLiGN in Browser** — Opens the dashboard

Desktop shortcut also provided for quick access.

---

## Distributing the Installer

Once built:

1. **Local use:**
   ```
   Copy: aLiGN\installer\output\aLiGN-Setup.exe
   To:   Your distribution folder or USB drive
   ```

2. **GitHub Release:**
   ```bash
   git tag v1.0.0
   git push --tags
   # Workflow auto-builds and uploads to Releases
   ```

3. **Web hosting:**
   Upload `aLiGN-Setup.exe` to your website for download.

---

## Troubleshooting

### Issue: `ISCC.exe not found`

**Solution:** Inno Setup 6 is not installed or not on PATH.
- [Download Inno Setup 6](https://jrsoftware.org/isdl.php)
- Run the installer and choose "Add to PATH"
- Restart Command Prompt

### Issue: Installer launches but Docker fails to start

**This is expected on first-run for users without Docker.**
- Installer prompts to download Docker Desktop
- User installs Docker, then reruns `start.bat`
- Everything else works normally

### Issue: Dashboard doesn't open after installation

**Possible causes:**
1. Docker hasn't fully started (wait 1-2 mins, refresh browser manually)
2. Services still initializing (check: `docker-compose logs backend`)
3. Browser blocked by firewall (allow `localhost:3000`)

**User workaround:**
1. Open browser manually
2. Visit `http://localhost:3000/dashboard`
3. If blank, wait 30 seconds and refresh

### Issue: Build fails with "File not found" error

**Solutions:**
- Verify paths in `setup.iss` match actual file locations
- Run compilation from repo **root** (not `installer/` directory)
- Check `.env.example` exists at `aLiGN/.env.example`

---

## Advanced: CI/CD (GitHub Actions)

The repo includes a GitHub Actions workflow that auto-builds on tag pushes:

```bash
git tag v1.0.0
git push --tags
```

The `.exe` is auto-uploaded to:
- **Workflow artifacts** (downloadable for 90 days)
- **GitHub Release** (permanent link)

See `.github/workflows/build-installer.yml` for details.

---

## File Structure

```
aLiGN/
├── installer/
│   ├── setup.iss              ← Main Inno Setup script (edit to customize)
│   ├── output/
│   │   └── aLiGN-Setup.exe   ← **FINAL INSTALLER** (created by build)
│   ├── scripts/
│   │   ├── start.bat          (auto-startup on install)
│   │   ├── stop.bat           (stop services)
│   │   └── open-browser.bat   (launch dashboard)
│   ├── BUILD.md               ← This file
│   └── README.md
├── docker-compose.yml         ← Included in installer
├── .env.example               ← Included in installer
├── backend/                   ← Included in installer
├── frontend/                  ← Included in installer
└── ...
```

---

## Performance Expectations

**On a typical machine (2023 laptop):**

| Phase | Duration | Notes |
|-------|----------|-------|
| Installer extract | 30–60 sec | Copying files |
| Docker build (first time) | 3–5 min | Building images from Dockerfiles |
| Services startup | 30–90 sec | Database init, migrations, health checks |
| **Total first-time** | **5–15 min** | Mostly waiting for Docker |
| Restart (subsequent) | 30–60 sec | Images cached, fast startup |

---

## Support & Documentation

- **aLiGN Repo:** [github.com/flencrypto/aLiGN](https://github.com/flencrypto/aLiGN)
- **Docker:** [docs.docker.com/desktop/install/windows](https://docs.docker.com/desktop/install/windows)
- **Inno Setup:** [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)

---

## Next Steps

1. ✅ Install **Inno Setup 6**
2. ✅ Run the build command (Option 1)
3. ✅ Test `aLiGN-Setup.exe` on a clean Windows machine
4. ✅ Distribute and get feedback!

**Happy building! 🚀**
