#!/usr/bin/env python3
"""
Quick setup for Cellpex 2FA testing
"""

import os
import sys
from pathlib import Path

def setup_cellpex_credentials():
    """Interactive setup for Cellpex credentials"""
    print("🔐 Cellpex Credentials Setup")
    print("=" * 40)
    
    # Check if already set
    if os.environ.get('CELLPEX_USERNAME') and os.environ.get('CELLPEX_PASSWORD'):
        print("✅ Cellpex credentials already set!")
        print(f"   Username: {os.environ.get('CELLPEX_USERNAME')}")
        print(f"   Password: {'*' * len(os.environ.get('CELLPEX_PASSWORD'))}")
        return True
    
    print("Enter your Cellpex credentials (these will be set as environment variables):")
    
    try:
        username = input("Cellpex Username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return False
        
        import getpass
        password = getpass.getpass("Cellpex Password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return False
        
        # Set environment variables for this session
        os.environ['CELLPEX_USERNAME'] = username
        os.environ['CELLPEX_PASSWORD'] = password
        
        print("✅ Credentials set successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {'*' * len(password)}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cellpex_enhanced_poster():
    """Test if enhanced poster is available for Cellpex"""
    print("\n🧪 Testing Cellpex Enhanced Poster...")
    
    try:
        from enhanced_platform_poster import ENHANCED_POSTERS
        
        if 'cellpex' in ENHANCED_POSTERS:
            print("✅ Enhanced Cellpex poster available!")
            print("   Features: Selenium automation + Gmail 2FA")
            return True
        else:
            print("⚠️  Enhanced poster not yet implemented for Cellpex")
            print("   Available platforms:", list(ENHANCED_POSTERS.keys()))
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced poster: {e}")
        return False

def run_live_2fa_test():
    """Run the live 2FA test for Cellpex"""
    print("\n🚀 Starting Cellpex Live 2FA Test...")
    
    try:
        from enhanced_platform_poster import test_platform_login_with_2fa
        
        print("⚠️  This will:")
        print("   1. Open Chrome browser")
        print("   2. Navigate to Cellpex login page")
        print("   3. Enter your credentials automatically")
        print("   4. Handle 2FA if required")
        print("   5. Check Gmail for verification codes")
        print("   6. Complete login process")
        
        proceed = input("\nProceed with live test? (y/N): ").lower().strip()
        
        if proceed == 'y':
            print("\n🔍 Starting test...")
            success = test_platform_login_with_2fa('cellpex')
            
            if success:
                print("\n🎉 Live 2FA test successful!")
                print("✅ Cellpex login automation working")
                print("✅ Gmail 2FA integration working")
            else:
                print("\n❌ Live 2FA test failed")
                print("💡 Check browser output for details")
        else:
            print("Test cancelled")
            
    except Exception as e:
        print(f"❌ Error running live test: {e}")

def main():
    """Main setup and testing flow"""
    print("🚀 Cellpex 2FA Testing Setup\n")
    
    # Step 1: Set up credentials
    if not setup_cellpex_credentials():
        return 1
    
    # Step 2: Test enhanced poster
    if not test_cellpex_enhanced_poster():
        print("\n💡 Note: Will use basic platform poster")
    
    # Step 3: Ask about live testing
    print("\n" + "=" * 50)
    print("🎯 Ready for Live Testing!")
    print("=" * 50)
    
    choice = input("\nWhat would you like to do?\n"
                  "1. Run live 2FA test now\n"
                  "2. Just verify setup (no browser test)\n"
                  "3. Exit\n"
                  "Choice (1-3): ").strip()
    
    if choice == '1':
        run_live_2fa_test()
    elif choice == '2':
        print("✅ Setup verified! Ready for testing.")
        print("💡 Run: python test_live_2fa_workflow.py cellpex")
    else:
        print("👋 Setup complete!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())