"""
Test Suite for Fallback Notification System
Run this to validate the notification system before packaging Windows desktop app.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.notification_utils import (
    get_user_settings,
    social_create_draft,
    gmail_draft_email,
    send_fallback_notifications
)
from backend.services.gmail_utils import fetch_latest_briefing_from_gmail
from backend.services.briefing_ingestion import run_daily_briefing_ingestion

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results for reporting."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
        logger.info(f"✅ PASS: {test_name} {message}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        logger.error(f"❌ FAIL: {test_name} - {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        logger.warning(f"⚠️ WARN: {test_name} - {message}")
    
    def print_summary(self):
        """Print test summary report."""
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        print(f"✅ Passed:   {len(self.passed)}")
        print(f"❌ Failed:   {len(self.failed)}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        print("="*70 + "\n")
        
        if self.failed:
            print("FAILED TESTS:")
            for test_name, error in self.failed:
                print(f"  ❌ {test_name}")
                print(f"     {error}")
            print()
        
        if self.warnings:
            print("WARNINGS:")
            for test_name, message in self.warnings:
                print(f"  ⚠️ {test_name}")
                print(f"     {message}")
            print()
        
        return len(self.failed) == 0


async def test_user_settings(results: TestResults):
    """Test 1: User settings retrieval."""
    try:
        settings = await get_user_settings()
        
        # Check permissions exist
        if "permissions" not in settings:
            results.add_fail("User Settings", "Missing 'permissions' key")
            return
        
        permissions = settings["permissions"]
        required = ["social_draft", "gmail_draft", "full_autopilot"]
        
        for key in required:
            if key not in permissions:
                results.add_fail("User Settings", f"Missing permission key: {key}")
                return
        
        # Check default safety values
        if permissions["full_autopilot"] is True:
            results.add_warning("User Settings", 
                              "full_autopilot is True (should be False by default for safety)")
        
        if permissions["social_draft"] and permissions["gmail_draft"]:
            results.add_pass("User Settings", 
                           f"social_draft={permissions['social_draft']}, "
                           f"gmail_draft={permissions['gmail_draft']}")
        else:
            results.add_warning("User Settings", 
                              "Both notification channels are disabled")
        
    except Exception as e:
        results.add_fail("User Settings", str(e))


async def test_social_draft_creation(results: TestResults):
    """Test 2: X/Twitter draft creation."""
    try:
        briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
        post_text = (
            f"@TheMrFlen Daily DC briefing email missing today ({briefing_date}). "
            f"No new intel pulled – check inbox or manual upload? #alignapp"
        )
        
        draft = await social_create_draft(
            platform="x",
            post_text=post_text,
            reason="Test notification system",
            auto_post=False
        )
        
        if "draft_id" not in draft:
            results.add_fail("Social Draft", "No draft_id returned")
            return
        
        if draft.get("status") != "draft_created":
            results.add_warning("Social Draft", f"Unexpected status: {draft.get('status')}")
        
        if draft.get("platform") != "x":
            results.add_fail("Social Draft", f"Wrong platform: {draft.get('platform')}")
            return
        
        results.add_pass("Social Draft", f"Created draft {draft['draft_id']}")
        
    except Exception as e:
        results.add_fail("Social Draft", str(e))


async def test_gmail_draft_creation(results: TestResults):
    """Test 3: Gmail draft email creation."""
    try:
        from backend.core.config import settings
        
        # Skip if Gmail not configured
        if not all([settings.GOOGLE_CLIENT_ID, 
                   settings.GOOGLE_CLIENT_SECRET, 
                   settings.GOOGLE_REFRESH_TOKEN]):
            results.add_warning("Gmail Draft", 
                              "Gmail OAuth not configured - skipping test")
            return
        
        briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
        subject = f"aLiGN Daily Briefing Missing - {briefing_date} [TEST]"
        body = (
            f"TEST EMAIL - Fallback notification system check\n\n"
            f"This is a test of the automated notification system.\n"
            f"If you see this, the Gmail draft creation is working correctly.\n\n"
            f"Generated: {datetime.utcnow().isoformat()}\n"
        )
        
        notification_email = settings.NOTIFICATION_EMAIL or "test@example.com"
        
        draft = await gmail_draft_email(
            to=[notification_email],
            subject=subject,
            body_plaintext=body,
            suggested_send_time_local=datetime.utcnow().isoformat()
        )
        
        if draft.get("status") == "error":
            results.add_fail("Gmail Draft", draft.get("error", "Unknown error"))
            return
        
        if "draft_id" not in draft:
            results.add_fail("Gmail Draft", "No draft_id returned")
            return
        
        results.add_pass("Gmail Draft", 
                        f"Created draft {draft['draft_id']} to {notification_email}")
        
    except Exception as e:
        results.add_fail("Gmail Draft", str(e))


async def test_gmail_fetch(results: TestResults):
    """Test 4: Gmail briefing fetch."""
    try:
        from backend.core.config import settings
        
        # Skip if Gmail not configured
        if not all([settings.GOOGLE_CLIENT_ID, 
                   settings.GOOGLE_CLIENT_SECRET, 
                   settings.GOOGLE_REFRESH_TOKEN]):
            results.add_warning("Gmail Fetch", 
                              "Gmail OAuth not configured - skipping test")
            return
        
        briefing_text = await fetch_latest_briefing_from_gmail()
        
        if briefing_text is None:
            results.add_warning("Gmail Fetch", 
                              "No briefing email found (expected if none available)")
        else:
            results.add_pass("Gmail Fetch", 
                           f"Fetched {len(briefing_text)} characters")
        
    except Exception as e:
        results.add_fail("Gmail Fetch", str(e))


async def test_fallback_orchestration(results: TestResults):
    """Test 5: Full fallback notification orchestration."""
    try:
        briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        result = await send_fallback_notifications(briefing_date)
        
        if "notifications_sent" not in result:
            results.add_fail("Fallback Orchestration", 
                           "Missing 'notifications_sent' in result")
            return
        
        notifications_sent = result["notifications_sent"]
        errors = result.get("errors", [])
        
        if len(notifications_sent) == 0 and len(errors) == 0:
            results.add_warning("Fallback Orchestration", 
                              "No notifications sent (permissions may be disabled)")
        elif len(errors) > 0:
            error_types = [e["type"] for e in errors]
            results.add_warning("Fallback Orchestration", 
                              f"Errors: {', '.join(error_types)}")
        else:
            notification_types = [n["type"] for n in notifications_sent]
            results.add_pass("Fallback Orchestration", 
                           f"Sent: {', '.join(notification_types)}")
        
    except Exception as e:
        results.add_fail("Fallback Orchestration", str(e))


async def test_environment_config(results: TestResults):
    """Test 6: Environment configuration."""
    try:
        from backend.core.config import settings
        
        # Check Gmail config
        if not settings.GOOGLE_CLIENT_ID:
            results.add_warning("Environment Config", 
                              "GOOGLE_CLIENT_ID not set")
        else:
            results.add_pass("Environment Config", 
                           f"GOOGLE_CLIENT_ID set ({settings.GOOGLE_CLIENT_ID[:20]}...)")
        
        if not settings.GOOGLE_CLIENT_SECRET:
            results.add_warning("Environment Config", 
                              "GOOGLE_CLIENT_SECRET not set")
        
        if not settings.GOOGLE_REFRESH_TOKEN:
            results.add_warning("Environment Config", 
                              "GOOGLE_REFRESH_TOKEN not set - run generate_gmail_token.py")
        
        # Check notification config
        if not settings.NOTIFICATION_EMAIL:
            results.add_warning("Environment Config", 
                              "NOTIFICATION_EMAIL not set")
        else:
            results.add_pass("Environment Config", 
                           f"NOTIFICATION_EMAIL set ({settings.NOTIFICATION_EMAIL})")
        
        if not settings.X_HANDLE:
            results.add_warning("Environment Config", 
                              "X_HANDLE not set")
        else:
            results.add_pass("Environment Config", 
                           f"X_HANDLE set (@{settings.X_HANDLE})")
        
    except Exception as e:
        results.add_fail("Environment Config", str(e))


async def test_windows_paths(results: TestResults):
    """Test 7: Windows file paths for desktop app."""
    try:
        # Check critical files exist
        backend_root = Path(__file__).parent.parent
        
        critical_files = [
            backend_root / "services" / "gmail_utils.py",
            backend_root / "services" / "notification_utils.py",
            backend_root / "services" / "briefing_ingestion.py",
            backend_root / "models" / "settings.py",
            backend_root / "core" / "config.py",
        ]
        
        missing = []
        for file_path in critical_files:
            if not file_path.exists():
                missing.append(file_path.name)
        
        if missing:
            results.add_fail("Windows Paths", 
                           f"Missing files: {', '.join(missing)}")
        else:
            results.add_pass("Windows Paths", 
                           f"All {len(critical_files)} critical files found")
        
        # Check client_secret.json location
        client_secret = backend_root / "client_secret.json"
        if client_secret.exists():
            results.add_pass("Windows Paths", 
                           "client_secret.json found in backend/")
        else:
            results.add_warning("Windows Paths", 
                              "client_secret.json not found (will need manual copy)")
        
    except Exception as e:
        results.add_fail("Windows Paths", str(e))


async def run_all_tests():
    """Run all tests and print summary."""
    results = TestResults()
    
    print("\n" + "="*70)
    print("FALLBACK NOTIFICATION SYSTEM - TEST SUITE")
    print("Windows Desktop Application Pre-Build Validation")
    print("="*70 + "\n")
    
    print("Running tests...\n")
    
    # Run all tests
    await test_environment_config(results)
    await test_windows_paths(results)
    await test_user_settings(results)
    await test_social_draft_creation(results)
    await test_gmail_draft_creation(results)
    await test_gmail_fetch(results)
    await test_fallback_orchestration(results)
    
    # Print summary
    success = results.print_summary()
    
    if success:
        print("✅ All tests passed! Ready for Windows desktop packaging.\n")
        return 0
    else:
        print("❌ Some tests failed. Fix issues before packaging.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
