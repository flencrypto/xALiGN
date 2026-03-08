# ✅ Pre-Build Validation Checklist

**Before building `aLiGN-Setup.exe` for distribution**

---

## 📋 Phase 1: File Verification

### Required Files Exist

Core notification system:
- [ ] `backend/models/settings.py` (UserSettings model)
- [ ] `backend/services/notification_utils.py` (4 notification functions)
- [ ] `backend/services/briefing_ingestion.py` (fallback integration)
- [ ] `backend/core/config.py` (NOTIFICATION_EMAIL, X_HANDLE)

Testing tools:
- [ ] `backend/tests/test_notifications.py` (7 automated tests)
- [ ] `backend/setup-gmail-oauth.bat` (OAuth wizard)
- [ ] `backend/test-notifications.bat` (test runner)
- [ ] `backend/tests/manual_test_notifications.py` (developer console)

Documentation:
- [ ] `backend/tests/README.md` (testing guide)
- [ ] `docs/gmail-fallback-setup.md` (OAuth setup)
- [ ] `docs/windows-desktop-setup.md` (Windows guide)
- [ ] `FALLBACK_NOTIFICATIONS.md` (quick reference)
- [ ] `TESTING-QUICK-START.md` (quick start)
- [ ] `WINDOWS-TESTING-SUMMARY.md` (implementation summary)

Installer configuration:
- [ ] `installer/setup.iss` (updated with new shortcuts)

---

## 🔒 Phase 2: Security Audit

### Sensitive Files NOT in Git

Check `.gitignore` excludes:
- [ ] `backend/client_secret.json`
- [ ] `backend/token.pickle`
- [ ] `backend/gmail_credentials.json`
- [ ] `.env`

### Verify No Hard-Coded Secrets

Check these files have NO hard-coded credentials:
- [ ] `backend/services/notification_utils.py`
- [ ] `backend/services/gmail_utils.py`
- [ ] `backend/services/briefing_ingestion.py`
- [ ] `backend/core/config.py`

All should use `os.getenv()` or Settings class.

---

## 🧪 Phase 3: Code Quality

### No Syntax Errors

Run linter/type checker:
```bash
cd backend
python -m py_compile models/settings.py
python -m py_compile services/notification_utils.py
python -m py_compile services/briefing_ingestion.py
python -m py_compile tests/test_notifications.py
python -m py_compile tests/manual_test_notifications.py
```

All should complete without errors.

### No Import Errors

Check imports resolve (ignore IDE warnings for sqlalchemy in Docker environment):
```bash
cd backend
python -c "from models.settings import UserSettings; print('✅ UserSettings imported')"
python -c "from services.notification_utils import send_fallback_notifications; print('✅ Notification utils imported')"
python -c "from services.briefing_ingestion import run_daily_briefing_ingestion; print('✅ Briefing ingestion imported')"
```

All should print "✅ ... imported"

---

## 🧪 Phase 4: Functional Testing

### Test Suite Execution

**Step 1: Run automated tests**
```cmd
cd backend
test-notifications.bat
```

**Expected output:**
```
========================================================================
TEST RESULTS SUMMARY
========================================================================
✅ Passed:   7 (or 5 if Gmail not configured yet)
❌ Failed:   0
⚠️ Warnings: 2 (if Gmail not configured - ACCEPTABLE)
========================================================================
```

**Minimum acceptable:** 5 passed, 0 failed, 2 warnings

**Step 2: Test OAuth wizard**
```cmd
cd backend
setup-gmail-oauth.bat
```

**Expected:** Wizard completes without errors, prints credentials

**Step 3: Manual testing (optional)**
```cmd
cd backend
python tests\manual_test_notifications.py
```

**Expected:** Menu displays, all options run without crashes

---

## 📦 Phase 5: Installer Configuration

### Setup.iss Validation

Check `installer/setup.iss` includes:

**Source files:**
- [ ] `Source: "..\\backend\\setup-gmail-oauth.bat"`
- [ ] `Source: "..\\backend\\test-notifications.bat"`
- [ ] `Source: "..\\backend\\tests\\test_notifications.py"`
- [ ] `Source: "..\\backend\\tests\\manual_test_notifications.py"`

**Start Menu icons:**
- [ ] `Name: "{group}\\Setup Gmail OAuth"`
- [ ] `Name: "{group}\\Test Notifications"`

**Tasks (optional desktop shortcuts):**
- [ ] `Name: "desktopgmailsetup"; Description: "Create Gmail OAuth Setup desktop icon"`

---

## 📚 Phase 6: Documentation Review

### User-Facing Documentation Complete

Check these files are comprehensive and accurate:

- [ ] **TESTING-QUICK-START.md**
  - 3-step setup process
  - Expected test results
  - Common issues and fixes

- [ ] **docs/windows-desktop-setup.md**
  - Windows app structure
  - User setup flow
  - Developer testing
  - Debugging guide
  - Pre-release checklist

- [ ] **docs/gmail-fallback-setup.md**
  - Gmail OAuth setup
  - client_secret.json download
  - Token generation
  - Troubleshooting

- [ ] **FALLBACK_NOTIFICATIONS.md**
  - System overview
  - Permission settings
  - Expected behavior

### Developer Documentation Complete

- [ ] **backend/tests/README.md**
  - Test file descriptions
  - Test scenarios
  - Common failures
  - CI/CD integration
  - Performance benchmarks

---

## 🔧 Phase 7: Environment Configuration

### .env.example Updated

Check `.env.example` includes:
```env
# Gmail OAuth (from setup-gmail-oauth.bat)
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REFRESH_TOKEN=your-refresh-token-here

# Notification Settings
NOTIFICATION_EMAIL=your-email@example.com
X_HANDLE=TheMrFlen
```

### Production .env Ready

Your actual `.env` should have:
- [ ] Valid `GOOGLE_CLIENT_ID`
- [ ] Valid `GOOGLE_CLIENT_SECRET`
- [ ] Valid `GOOGLE_REFRESH_TOKEN`
- [ ] Real email in `NOTIFICATION_EMAIL`
- [ ] Correct `X_HANDLE`

---

## 🏗️ Phase 8: Build Test

### Build Installer

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

**Expected:**
- No errors during compilation
- Output file: `installer\output\aLiGN-Setup.exe`
- File size: ~150-200 MB (includes Docker images)

### Test Installer (Critical!)

**On a clean Windows 10/11 machine:**

1. **Install**
   ```
   Run aLiGN-Setup.exe
   ```
   - [ ] Installation completes without errors
   - [ ] Services auto-start
   - [ ] Browser opens to http://localhost:3000

2. **Verify Start Menu**
   ```
   Start > aLiGN
   ```
   - [ ] "Start aLiGN" present
   - [ ] "Stop aLiGN" present
   - [ ] "Setup Gmail OAuth" present ← NEW
   - [ ] "Test Notifications" present ← NEW
   - [ ] "Uninstall" present

3. **Test OAuth Wizard**
   ```
   Start > aLiGN > Setup Gmail OAuth
   ```
   - [ ] Batch script launches
   - [ ] Python check passes
   - [ ] client_secret.json missing message (expected)
   - [ ] Instructions display correctly

4. **Test Suite Runner**
   ```
   Start > aLiGN > Test Notifications
   ```
   - [ ] Batch script launches
   - [ ] Python check passes
   - [ ] Tests run automatically
   - [ ] Results display correctly

---

## 🎯 Phase 9: Acceptance Criteria

### Core Functionality

- [ ] Daily briefing ingestion works (with email present)
- [ ] Fallback notifications trigger (when email missing)
- [ ] X drafts created successfully
- [ ] Gmail drafts created successfully
- [ ] User settings retrieved with safe defaults
- [ ] Logging captures all events

### Windows Desktop Experience

- [ ] One-click installer works
- [ ] Services auto-start on installation
- [ ] OAuth wizard accessible from Start Menu
- [ ] Test suite accessible from Start Menu
- [ ] Non-technical users can complete setup
- [ ] Troubleshooting documentation clear

### Developer Experience

- [ ] All tests pass (or expected warnings only)
- [ ] Manual test console works
- [ ] Documentation comprehensive
- [ ] Error messages helpful
- [ ] CI/CD integration possible (future)

---

## 📊 Final Validation Summary

### Must-Have (Blockers)

- [ ] All 7 tests pass OR only expected warnings
- [ ] No hard-coded secrets in code
- [ ] Sensitive files in `.gitignore`
- [ ] Installer builds without errors
- [ ] Start Menu shortcuts created
- [ ] OAuth wizard launches successfully
- [ ] Test suite launches successfully

### Should-Have (Important)

- [ ] Tested on clean Windows machine
- [ ] Documentation reviewed by second person
- [ ] User acceptance testing completed
- [ ] Common issues documented
- [ ] Support resources linked in README

### Nice-to-Have (Optional)

- [ ] CI/CD pipeline configured
- [ ] Automated installer testing
- [ ] Telemetry/analytics integration
- [ ] User feedback mechanism

---

## 🚦 Go/No-Go Decision

### ✅ GO - Ready for Distribution

All "Must-Have" items checked:
- Code quality verified
- Security audit passed
- Functional testing successful
- Installer tested on clean machine
- Documentation complete

### ⚠️ CONDITIONAL GO - Acceptable with Warnings

Most "Must-Have" items checked, minor warnings:
- Gmail OAuth not configured on build machine (acceptable - end users configure)
- Some tests show warnings (acceptable if expected)
- Documentation has minor typos (acceptable if not critical)

### ❌ NO-GO - Not Ready

Any "Must-Have" item failed:
- Tests fail (not warnings)
- Hard-coded secrets found
- Installer build errors
- Start Menu shortcuts missing
- OAuth wizard doesn't launch

---

## 📝 Sign-Off

**Tested by:** ___________________  
**Date:** ___________________  
**Build version:** ___________________  
**Test results:** ✅ PASS / ⚠️ CONDITIONAL / ❌ FAIL  

**Notes:**
```
[Add any observations, issues found, or recommendations]
```

**Approved for distribution:** ☐ YES  ☐ NO

---

## 🚀 Distribution Steps (After Sign-Off)

1. **Tag release in Git**
   ```bash
   git tag -a v1.0.0-notifications -m "Windows desktop with fallback notifications"
   git push origin v1.0.0-notifications
   ```

2. **Upload installer**
   - Location: `installer\output\aLiGN-Setup.exe`
   - Destination: File server / SharePoint / GitHub Releases

3. **Create release notes**
   - New features: Fallback notifications, OAuth wizard, test suite
   - Installation instructions
   - Known issues (if any)
   - Support contact

4. **Notify users**
   - Email distribution list
   - Update documentation site
   - Post in team channels

---

## ⚡ One-Click Local Execution

Run tests and build the installer in one command:

```cmd
run-test-and-deploy.bat
```

This script:
- Runs `backend\test-notifications.bat`
- Aborts immediately if tests fail
- Builds installer via Inno Setup only on test pass
- Confirms output at `installer\output\aLiGN-Setup.exe`

---

**Ready to ship!** 🎉
