#!/usr/bin/env python3
"""
Test the enhanced 2FA architecture with LLM-based code extraction
"""

import os
import sys
from dotenv import load_dotenv

def test_enhanced_cellpex_2fa():
    """Test the enhanced 2FA flow with Cellpex"""
    print("🚀 Testing Enhanced 2FA Architecture for Cellpex...")
    
    # Load environment variables
    load_dotenv()
    
    # Check credentials
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        print("💡 Make sure CELLPEX_USERNAME and CELLPEX_PASSWORD are set")
        return False
        
    print(f"✅ Credentials found:")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)}")
    print(f"   OpenAI API: {'✅ Available' if openai_key else '⚠️ Not set (will use regex fallback)'}")
    
    try:
        # Import the universal platform handler
        from universal_2fa_platform import quick_platform_setup
        
        print("\n🔧 Creating Cellpex platform handler...")
        platform = quick_platform_setup('cellpex')
        
        print("📧 Checking Gmail service...")
        if platform.gmail_service and platform.gmail_service.is_available():
            print("✅ Gmail service connected and authenticated")
        else:
            print("❌ Gmail service not available - 2FA won't work")
            return False
        
        print(f"\n⚠️  This will:")
        print(f"   1. Open browser to Cellpex login page")
        print(f"   2. Enter your credentials: {username}")
        print(f"   3. Detect if 2FA is required")
        print(f"   4. Wait 60 seconds for 2FA email")
        print(f"   5. Search Gmail for Cellpex emails")
        print(f"   6. Use {'LLM' if openai_key else 'regex'} to extract authentication code")
        print(f"   7. Enter code and complete login")
        
        proceed = input("\nProceed with live test? (y/N): ").lower().strip()
        
        if proceed == 'y':
            print("\n🧪 Starting enhanced 2FA test...")
            
            # Test the enhanced login flow
            success = platform.login_with_2fa()
            
            if success:
                print(f"\n🎉 Enhanced 2FA test successful!")
                print(f"✅ Successfully logged into Cellpex with automated 2FA")
                # Take screenshot for verification
                platform.driver.save_screenshot("cellpex_enhanced_2fa_success.png")
                print(f"📸 Screenshot saved: cellpex_enhanced_2fa_success.png")
            else:
                print(f"\n❌ Enhanced 2FA test failed")
                platform.driver.save_screenshot("cellpex_enhanced_2fa_failed.png")
                print(f"📸 Debug screenshot saved: cellpex_enhanced_2fa_failed.png")
                
            return success
        else:
            print("Test cancelled")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'platform' in locals():
            print("🔒 Closing browser...")
            platform.driver.quit()


def test_llm_code_extraction():
    """Test LLM code extraction without browser automation"""
    print("🤖 Testing LLM Code Extraction...")
    
    # Sample email content for testing
    sample_emails = [
        {
            'subject': 'Cellpex Security Code',
            'content': 'Your verification code is 123456. Please enter this code to complete your login.'
        },
        {
            'subject': 'Authentication Required',
            'content': 'Hello! Your Cellpex authentication code: 789012. This code expires in 10 minutes.'
        },
        {
            'subject': 'Login Verification',
            'content': 'To complete your login, please use code 456789.'
        }
    ]
    
    try:
        from enhanced_platform_poster import Enhanced2FAMarketplacePoster
        
        # Create a mock instance to test LLM extraction
        class MockPlatform(Enhanced2FAMarketplacePoster):
            PLATFORM = "TEST"
            
            def __init__(self):
                pass  # Skip driver initialization for testing
        
        mock = MockPlatform()
        
        print("📧 Testing code extraction on sample emails...")
        
        for i, email in enumerate(sample_emails):
            print(f"\n📨 Email {i+1}: '{email['subject']}'")
            print(f"Content: {email['content'][:60]}...")
            
            # Test LLM extraction
            code = mock._llm_extract_auth_code(email['content'], email['subject'])
            
            if code:
                print(f"✅ Extracted code: {code}")
            else:
                print(f"❌ No code extracted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM extraction: {e}")
        return False


def main():
    """Main test runner"""
    print("🧪 Enhanced 2FA Architecture Tests\n")
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'llm':
            test_llm_code_extraction()
        elif test_type == 'cellpex':
            test_enhanced_cellpex_2fa()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available tests: llm, cellpex")
    else:
        print("Available tests:")
        print("  python test_enhanced_2fa.py llm      - Test LLM code extraction")
        print("  python test_enhanced_2fa.py cellpex  - Test full Cellpex 2FA flow")
        
        choice = input("\nWhich test would you like to run? (llm/cellpex): ").lower().strip()
        
        if choice == 'llm':
            test_llm_code_extraction()
        elif choice == 'cellpex':
            test_enhanced_cellpex_2fa()
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()