"""
Manual test script - Run individual notification components
For debugging and development
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.notification_utils import (
    get_user_settings,
    social_create_draft,
    gmail_draft_email,
    send_fallback_notifications
)
from datetime import datetime


async def test_user_settings():
    """Test: Get user settings."""
    print("\n" + "="*70)
    print("TEST: Get User Settings")
    print("="*70)
    
    settings = await get_user_settings()
    
    print("\nRetrieved settings:")
    print(f"  Permissions:")
    for key, value in settings.get("permissions", {}).items():
        print(f"    • {key}: {value}")
    print(f"\n  Notification Email: {settings.get('notification_email', 'Not set')}")
    print(f"  X Handle: @{settings.get('x_handle', 'Not set')}")
    print(f"  Timezone: {settings.get('timezone', 'Not set')}")
    

async def test_x_draft():
    """Test: Create X/Twitter draft."""
    print("\n" + "="*70)
    print("TEST: Create X/Twitter Draft")
    print("="*70)
    
    briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
    post_text = (
        f"@TheMrFlen Daily DC briefing email missing today ({briefing_date}). "
        f"No new intel pulled – check inbox or manual upload? #alignapp"
    )
    
    print(f"\nCreating draft with text:")
    print(f"  {post_text}\n")
    
    draft = await social_create_draft(
        platform="x",
        post_text=post_text,
        reason="Manual test - notification system validation",
        auto_post=False
    )
    
    print("Draft created:")
    print(f"  Draft ID: {draft.get('draft_id')}")
    print(f"  Platform: {draft.get('platform')}")
    print(f"  Status: {draft.get('status')}")
    print(f"  Created: {draft.get('created_at')}")


async def test_email_draft():
    """Test: Create Gmail draft email."""
    print("\n" + "="*70)
    print("TEST: Create Gmail Draft Email")
    print("="*70)
    
    from backend.core.config import settings
    
    if not all([settings.GOOGLE_CLIENT_ID, 
               settings.GOOGLE_CLIENT_SECRET, 
               settings.GOOGLE_REFRESH_TOKEN]):
        print("\n⚠️  Gmail OAuth not configured - skipping test")
        print("\nTo configure:")
        print("  1. Run: backend\\setup-gmail-oauth.bat")
        print("  2. Follow the wizard instructions")
        print("  3. Update .env with credentials")
        print("  4. Run this test again")
        return
    
    briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
    notification_email = settings.NOTIFICATION_EMAIL or "test@example.com"
    
    subject = f"aLiGN Daily Briefing Missing - {briefing_date} [TEST]"
    body = (
        f"TEST EMAIL - Manual notification system validation\n\n"
        f"This is a test of the Gmail draft creation functionality.\n"
        f"If you see this draft in your Gmail, the system is working correctly.\n\n"
        f"Briefing Date: {briefing_date}\n"
        f"Generated: {datetime.utcnow().isoformat()}\n"
        f"Test Mode: Manual\n"
    )
    
    print(f"\nCreating draft email:")
    print(f"  To: {notification_email}")
    print(f"  Subject: {subject}\n")
    
    draft = await gmail_draft_email(
        to=[notification_email],
        subject=subject,
        body_plaintext=body,
        suggested_send_time_local=datetime.utcnow().isoformat()
    )
    
    if draft.get("status") == "error":
        print(f"❌ Error: {draft.get('error')}")
    else:
        print("✅ Draft created:")
        print(f"  Draft ID: {draft.get('draft_id')}")
        print(f"  Message ID: {draft.get('message_id')}")
        print(f"  Status: {draft.get('status')}")
        print(f"  Created: {draft.get('created_at')}")


async def test_full_fallback():
    """Test: Full fallback notification orchestration."""
    print("\n" + "="*70)
    print("TEST: Full Fallback Notification Orchestration")
    print("="*70)
    
    briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    print(f"\nTriggering fallback for date: {briefing_date}\n")
    
    result = await send_fallback_notifications(briefing_date)
    
    print("Fallback result:")
    print(f"  Briefing Date: {result.get('briefing_date')}")
    print(f"\n  Notifications Sent: {len(result.get('notifications_sent', []))}")
    
    for notif in result.get('notifications_sent', []):
        print(f"    • {notif['type']}: {notif['status']}")
        if 'draft_id' in notif:
            print(f"      Draft ID: {notif['draft_id']}")
    
    if result.get('errors'):
        print(f"\n  Errors: {len(result['errors'])}")
        for error in result['errors']:
            print(f"    • {error['type']}: {error['error']}")
    else:
        print("\n  ✅ No errors")


async def interactive_menu():
    """Interactive menu for manual testing."""
    while True:
        print("\n" + "="*70)
        print("MANUAL NOTIFICATION TESTING MENU")
        print("="*70)
        print("\nAvailable tests:")
        print("  1. Get User Settings")
        print("  2. Create X/Twitter Draft")
        print("  3. Create Gmail Draft Email")
        print("  4. Full Fallback Orchestration")
        print("  5. Run All Tests")
        print("  6. Exit")
        print("\n" + "="*70)
        
        choice = input("\nEnter test number (1-6): ").strip()
        
        if choice == "1":
            await test_user_settings()
        elif choice == "2":
            await test_x_draft()
        elif choice == "3":
            await test_email_draft()
        elif choice == "4":
            await test_full_fallback()
        elif choice == "5":
            await test_user_settings()
            await test_x_draft()
            await test_email_draft()
            await test_full_fallback()
        elif choice == "6":
            print("\nExiting...")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-6.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("aLiGN - Manual Notification Testing")
    print("Windows Desktop Application - Developer Console")
    print("="*70)
    
    try:
        asyncio.run(interactive_menu())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
