# Windows Desktop Application - Setup & Testing Guide

## 🪟 Windows Desktop App Structure

The aLiGN Windows installer packages the entire application (frontend + backend) as a self-contained desktop app using Docker Compose.

### Key Components

```
C:\Program Files\aLiGN\
├── backend/
│   ├── client_secret.json         ← Gmail OAuth credentials (user provides)
│   ├── token.pickle               ← Generated OAuth token
│   ├── setup-gmail-oauth.bat      ← OAuth setup wizard (NEW)
│   ├── test-notifications.bat     ← Notification test suite (NEW)
│   ├── scripts/
│   │   └── generate_gmail_token.py
│   ├── services/
│   │   ├── gmail_utils.py
│   │   ├── notification_utils.py   ← Fallback notifications (NEW)
│   │   └── briefing_ingestion.py
│   ├── models/
│   │   └── settings.py             ← User settings (NEW)
│   └── tests/
│       └── test_notifications.py   ← Test suite (NEW)
├── frontend/
├── docker-compose.yml
├── .env                            ← Created on first run
├── start.bat                       ← Start services
├── stop.bat                        ← Stop services
└── open-browser.bat                ← Open dashboard
```

---

## 🚀 User Setup Flow (End-User Experience)

### Step 1: Install aLiGN (Automated)

1. Run `aLiGN-Setup.exe`
2. Choose installation directory (default: `C:\Program Files\aLiGN`)
3. Installer automatically:
   - Extracts files
   - Creates `.env` from `.env.example`
   - Starts Docker services
   - Opens dashboard at `http://localhost:3000`

### Step 2: Gmail OAuth Setup (Interactive Wizard)

```cmd
cd "C:\Program Files\aLiGN\backend"
setup-gmail-oauth.bat
```

**Wizard steps:**
1. Checks for Python installation
2. Checks for `client_secret.json`
   - If missing → Shows Google Cloud Console setup instructions
   - Pauses for user to download and copy file
3. Installs required Python packages (if needed)
4. Opens browser for Google OAuth consent
5. Saves `token.pickle`
6. Prints credentials to copy into `.env`

**User actions:**
1. Follow wizard instructions to get `client_secret.json`
2. Grant Gmail access in browser
3. Copy printed credentials into `.env`
4. Add `NOTIFICATION_EMAIL=your-email@example.com` to `.env`
5. Run `stop.bat` then `start.bat` to restart services

### Step 3: Test Notifications (Validation)

```cmd
cd "C:\Program Files\aLiGN\backend"
test-notifications.bat
```

**Test suite runs:**
- ✅ Environment configuration check
- ✅ Windows file paths validation
- ✅ User settings retrieval
- ✅ X/Twitter draft creation
- ✅ Gmail draft creation (if OAuth configured)
- ✅ Gmail briefing fetch (if OAuth configured)
- ✅ Full fallback orchestration

**Output:**
```
========================================================================
TEST RESULTS SUMMARY
========================================================================
✅ Passed:   7
❌ Failed:   0
⚠️ Warnings: 2
========================================================================

✅ All tests passed! Ready for Windows desktop packaging.
```

---

## 🛠️ Developer Testing (Pre-Build Validation)

Before building the Windows installer, run the test suite to ensure everything works:

### Option 1: Quick Test (Python)

```cmd
cd backend
python tests\test_notifications.py
```

### Option 2: Full Test (Batch Script)

```cmd
cd backend
test-notifications.bat
```

### Expected Results

| Test | Expected | Notes |
|------|----------|-------|
| **Environment Config** | PASS with warnings | Warnings if OAuth not set up yet (OK) |
| **Windows Paths** | PASS | All critical files exist |
| **User Settings** | PASS | Permissions retrieved correctly |
| **Social Draft** | PASS | X draft created with draft_id |
| **Gmail Draft** | PASS or WARN | WARN if OAuth not configured (OK) |
| **Gmail Fetch** | PASS or WARN | WARN if no briefing email (OK) |
| **Fallback Orchestration** | PASS | Notifications sent successfully |

---

## 🔧 Debugging Common Issues

### Issue 1: Gmail OAuth Not Configured

**Symptoms:**
- `test_notifications.py` shows warnings for Gmail tests
- "Gmail OAuth credentials not configured" in logs

**Fix:**
```cmd
cd backend
setup-gmail-oauth.bat
```

Follow wizard instructions to set up OAuth.

### Issue 2: client_secret.json Missing

**Symptoms:**
- OAuth setup wizard shows error
- "client_secret.json not found"

**Fix:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID → Desktop app
3. Download JSON
4. Rename to `client_secret.json`
5. Copy to `backend/` directory
6. Run `setup-gmail-oauth.bat` again

### Issue 3: Tests Fail with "Module not found"

**Symptoms:**
```
ModuleNotFoundError: No module named 'google_auth_oauthlib'
```

**Fix:**
```cmd
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Issue 4: Notification Emails Not Sent

**Symptoms:**
- Tests pass but no email drafts created
- "No notification email configured" in logs

**Fix:**
Add to `.env`:
```env
NOTIFICATION_EMAIL=your-email@example.com
```

Restart backend: `stop.bat` then `start.bat`

### Issue 5: X Drafts Show as "draft_created" but Not in X

**Expected Behavior:**
The current implementation logs drafts but doesn't actually post to X/Twitter. This is intentional (safety first).

**To integrate with X API:**
1. Get X API credentials (v2 API)
2. Update `notification_utils.py` → `social_create_draft()` to call X API
3. Set `full_autopilot=True` in user settings (optional auto-posting)

---

## 📦 Building the Installer (Developer)

### Prerequisites

1. **Inno Setup 6** installed
   - Download: https://jrsoftware.org/isdl.php
   - Install to default location

2. **All tests passing**
   ```cmd
   cd backend
   test-notifications.bat
   ```

3. **Clean build** (remove temp files)
   ```cmd
   docker-compose down -v
   rd /s /q backend\__pycache__
   rd /s /q frontend\node_modules
   rd /s /q frontend\.next
   ```

### Build Command

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

### Output

```
installer\output\aLiGN-Setup.exe
```

### Testing the Installer

1. **Uninstall** previous version (if any)
2. **Run** `aLiGN-Setup.exe`
3. **Verify** services start automatically
4. **Verify** dashboard opens in browser
5. **Run** `setup-gmail-oauth.bat` to test OAuth wizard
6. **Run** `test-notifications.bat` to validate notifications

---

## 🔐 Security Considerations for Desktop App

### Files Excluded from Installer

These files should **NEVER** be included in the installer package:

- ❌ `backend/client_secret.json` - User provides their own
- ❌ `backend/token.pickle` - Generated per-user
- ❌ `backend/.env` - Created on first run from `.env.example`
- ❌ `backend/__pycache__/` - Python cache
- ❌ `frontend/node_modules/` - Node.js dependencies
- ❌ `frontend/.next/` - Next.js build artifacts

### Files Included in Installer

✅ ALL source code (Python, JavaScript, React)  
✅ `docker-compose.yml`  
✅ `.env.example` (template only)  
✅ Helper scripts (`start.bat`, `stop.bat`, `setup-gmail-oauth.bat`, `test-notifications.bat`)  
✅ Documentation (`docs/`)

### User Data Storage

User-specific data is stored in the installation directory:

```
C:\Program Files\aLiGN\
├── .env                    ← User's environment config
├── align.db                ← SQLite database (if not using PostgreSQL)
├── uploads/                ← User uploads
├── backend/
│   ├── client_secret.json  ← User's OAuth credentials
│   └── token.pickle        ← User's OAuth token
```

**Uninstall behavior:**
- Installer removes all program files
- User data (`.env`, `token.pickle`, `align.db`) is preserved
- User can manually delete if needed

---

## 📝 Checklist Before Release

### Pre-Build

- [ ] All tests pass (`test-notifications.bat`)
- [ ] Documentation updated (`docs/gmail-fallback-setup.md`)
- [ ] OAuth wizard tested (`setup-gmail-oauth.bat`)
- [ ] Clean build (no temp files)
- [ ] Version number updated (`installer\setup.iss`)

### Post-Build

- [ ] Installer runs without errors
- [ ] Services auto-start on install
- [ ] Dashboard opens automatically
- [ ] OAuth wizard accessible from Start Menu
- [ ] Test suite accessible from backend directory
- [ ] Uninstall removes all program files

### User Testing

- [ ] Fresh install on clean Windows 10/11 machine
- [ ] OAuth setup completes successfully
- [ ] Notification tests pass
- [ ] Daily briefing ingestion works (with real email)
- [ ] Fallback notifications trigger when no email found

---

## 🆘 Support Resources

### Documentation

- **Full setup guide**: `docs/gmail-fallback-setup.md`
- **Windows install guide**: `docs/windows-install.md`
- **Quick reference**: `FALLBACK_NOTIFICATIONS.md`

### Interactive Wizards

- **OAuth setup**: `backend\setup-gmail-oauth.bat`
- **Notification test**: `backend\test-notifications.bat`

### Logs

- **Backend logs**: Check Docker Desktop → Containers → backend logs
- **Frontend logs**: Check Docker Desktop → Containers → frontend logs
- **Scheduler logs**: Search for "daily_briefing_ingestion" in backend logs

---

**Ready for production deployment!** 🚀
