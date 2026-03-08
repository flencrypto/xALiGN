# 🚀 Testing Quick Start Guide

## Windows Desktop Testing - 3 Easy Steps

### Step 1: Setup Gmail OAuth (First Time Only)

**From Start Menu:**
```
Start → aLiGN → Setup Gmail OAuth
```

**Or manually:**
```cmd
cd backend
setup-gmail-oauth.bat
```

**What it does:**
- ✅ Checks Python installation
- ✅ Validates client_secret.json (guides you if missing)
- ✅ Installs required packages
- ✅ Opens browser for Google OAuth
- ✅ Prints credentials for `.env`

**Time:** 3-5 minutes

---

### Step 2: Configure Environment

**Edit `.env` file:**
```env
# Add these after OAuth wizard completes:
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REFRESH_TOKEN=your-refresh-token-here

# Add your notification email:
NOTIFICATION_EMAIL=your-email@example.com

# X handle already set:
X_HANDLE=TheMrFlen
```

**Time:** 1 minute

---

### Step 3: Run Tests

**From Start Menu:**
```
Start → aLiGN → Test Notifications
```

**Or manually:**
```cmd
cd backend
test-notifications.bat
```

**Expected output:**
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

**Time:** 10-15 seconds

---

## What Gets Tested?

| # | Test | What It Checks |
|---|------|----------------|
| 1 | **Environment Config** | All .env variables set correctly |
| 2 | **Windows Paths** | Critical files exist in installation |
| 3 | **User Settings** | Permission retrieval works |
| 4 | **Social Draft** | X/Twitter draft creation |
| 5 | **Gmail Draft** | Email draft via Gmail API |
| 6 | **Gmail Fetch** | Daily briefing email fetch |
| 7 | **Orchestration** | Full fallback notification flow |

---

## Test Results Explained

### ✅ PASS - Perfect!
Everything works correctly. No action needed.

### ⚠️ WARN - Expected
Common warnings (not errors):
- "Gmail OAuth not configured" - Run setup wizard
- "No briefing email found" - Normal during testing
- "client_secret.json missing" - Download from Google Cloud

### ❌ FAIL - Needs Attention
- Missing .env variables
- Python packages not installed
- Invalid Gmail credentials
- File paths incorrect

---

## Common Issues & Fixes

### Issue 1: "Python not found"

**Symptom:**
```
'python' is not recognized as an internal or external command
```

**Fix:**
Install Python 3.11 from https://www.python.org/downloads/

---

### Issue 2: "client_secret.json not found"

**Symptom:**
```
ERROR: client_secret.json not found in backend directory
```

**Fix:**
1. Go to https://console.cloud.google.com
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials
4. Download as `client_secret.json`
5. Copy to `C:\Program Files\aLiGN\backend\`

---

### Issue 3: "Missing .env variables"

**Symptom:**
```
⚠️ WARN: GOOGLE_CLIENT_ID not set in environment
```

**Fix:**
1. Run OAuth wizard: `setup-gmail-oauth.bat`
2. Copy printed credentials to `.env`
3. Restart Docker services

---

### Issue 4: "Gmail tests fail"

**Symptom:**
```
❌ FAIL: test_gmail_draft_creation()
```

**Fix:**
Check OAuth token is valid:
```cmd
python backend\scripts\generate_gmail_token.py
```

Re-authorize if expired.

---

## Developer Testing

### Interactive Console

For detailed debugging:

```cmd
cd backend
python tests\manual_test_notifications.py
```

**Menu options:**
1. Get User Settings - See all permissions
2. Create X/Twitter Draft - Test social notifications
3. Create Gmail Draft Email - Test email notifications
4. Full Fallback Orchestration - End-to-end test
5. Run All Tests - Complete suite
6. Exit

---

## Production Deployment Checklist

Before building installer for distribution:

- [ ] OAuth wizard tested on clean Windows machine
- [ ] All 7 tests pass (or expected warnings only)
- [ ] Documentation reviewed (`docs/gmail-fallback-setup.md`)
- [ ] `.gitignore` excludes sensitive files
- [ ] Installer includes all batch scripts
- [ ] Start Menu shortcuts created correctly
- [ ] Services auto-start after installation
- [ ] Notification emails arrive in drafts
- [ ] X drafts visible in logging

---

## Build Installer

Once all tests pass:

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

**Output:** `installer\output\aLiGN-Setup.exe`

**Includes:**
- ✅ Frontend (Next.js)
- ✅ Backend (FastAPI)
- ✅ Docker Compose
- ✅ OAuth setup wizard
- ✅ Test suite
- ✅ Documentation
- ✅ Start Menu shortcuts

---

## Support Resources

| Resource | Location |
|----------|----------|
| **Setup Guide** | `docs/gmail-fallback-setup.md` |
| **Windows Guide** | `docs/windows-desktop-setup.md` |
| **Test Documentation** | `backend/tests/README.md` |
| **Quick Reference** | `FALLBACK_NOTIFICATIONS.md` |
| **OAuth Wizard** | `backend/setup-gmail-oauth.bat` |
| **Test Runner** | `backend/test-notifications.bat` |

---

## Success Criteria

✅ **Ready for Production** means:

1. OAuth wizard completes without errors
2. All 7 tests pass (warnings OK)
3. Gmail drafts created successfully
4. X drafts logged correctly
5. User settings retrieved with safe defaults
6. Fallback orchestration runs end-to-end
7. Start Menu shortcuts launch tools

---

**Need help?** Check `docs/windows-desktop-setup.md` for troubleshooting! 🛠️
