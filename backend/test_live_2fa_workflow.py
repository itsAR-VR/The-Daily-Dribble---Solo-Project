#!/usr/bin/env python3
"""
Test live 2FA workflows with actual platform logins
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_live_2fa_workflow(platform):
    """Test complete 2FA workflow with real platform"""
    print(f"🚀 Testing live 2FA workflow for {platform.upper()}...")
    
    try:
        from enhanced_platform_poster import test_platform_login_with_2fa
        
        print("⚠️  This will:")
        print("   1. Open browser to platform login page")
        print("   2. Enter your credentials")
        print("   3. Trigger 2FA if required")
        print("   4. Check Gmail for verification code")
        print("   5. Complete login automatically")
        
        proceed = input("\nProceed with live test? (y/N): ").lower().strip()
        
        if proceed == 'y':
            success = test_platform_login_with_2fa(platform)
            if success:
                print(f"✅ Live 2FA workflow successful for {platform}!")
            else:
                print(f"❌ Live 2FA workflow failed for {platform}")
        else:
            print("Test cancelled")
            
    except Exception as e:
        print(f"❌ Error in live test: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_live_2fa_workflow.py <platform>")
        print("Platforms: gsmexchange, cellpex, kardof, hubx, handlot")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    test_live_2fa_workflow(platform)
