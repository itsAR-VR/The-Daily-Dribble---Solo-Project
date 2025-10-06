#!/usr/bin/env python3
"""
Setup and test platform credentials for live 2FA workflows
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Platform credentials needed for Railway
REQUIRED_CREDENTIALS = {
    'gsmexchange': {
        'username_var': 'GSMEXCHANGE_USERNAME',
        'password_var': 'GSMEXCHANGE_PASSWORD',
        'description': 'GSM Exchange marketplace credentials'
    },
    'cellpex': {
        'username_var': 'CELLPEX_USERNAME', 
        'password_var': 'CELLPEX_PASSWORD',
        'description': 'Cellpex marketplace credentials'
    },
    'kadorf': {
        'username_var': 'KADORF_USERNAME',
        'password_var': 'KADORF_PASSWORD', 
        'description': 'Kadorf marketplace credentials'
    },
    'hubx': {
        'username_var': 'HUBX_USERNAME',
        'password_var': 'HUBX_PASSWORD',
        'description': 'HubX marketplace credentials'
    },
    'handlot': {
        'username_var': 'HANDLOT_USERNAME',
        'password_var': 'HANDLOT_PASSWORD',
        'description': 'Handlot marketplace credentials'
    }
}

def check_local_credentials():
    """Check which platform credentials are available locally"""
    print("🔍 Checking local platform credentials...\n")
    
    available = []
    missing = []
    
    for platform, config in REQUIRED_CREDENTIALS.items():
        username = os.environ.get(config['username_var'])
        password = os.environ.get(config['password_var'])
        
        if username and password:
            print(f"✅ {platform.upper()}: {config['description']}")
            print(f"   👤 Username: {username}")
            print(f"   🔐 Password: {'*' * len(password)}")
            available.append(platform)
        else:
            print(f"❌ {platform.upper()}: Missing credentials")
            if not username:
                print(f"   Missing: {config['username_var']}")
            if not password:
                print(f"   Missing: {config['password_var']}")
            missing.append(platform)
        print()
    
    return available, missing

def generate_railway_env_setup():
    """Generate Railway environment variable setup commands"""
    print("🚀 Railway Environment Variables Setup\n")
    print("To set up credentials on Railway, run these commands:")
    print("=" * 60)
    
    for platform, config in REQUIRED_CREDENTIALS.items():
        print(f"\n# {config['description']}")
        print(f"railway variables set {config['username_var']}=your_{platform}_username")
        print(f"railway variables set {config['password_var']}=your_{platform}_password")
    
    print("\n# Additional required variables")
    print("railway variables set OPENAI_API_KEY=your_openai_api_key")
    print("railway variables set CHROME_BIN=/usr/bin/google-chrome")
    print("railway variables set CHROME_PATH=/usr/bin/google-chrome")
    
    print("\n" + "=" * 60)
    print("💡 Replace 'your_platform_username' and 'your_platform_password' with actual credentials")

def test_platform_login_simulation(platform):
    """Simulate platform login to test credentials"""
    if platform not in REQUIRED_CREDENTIALS:
        print(f"❌ Unknown platform: {platform}")
        return False
    
    config = REQUIRED_CREDENTIALS[platform]
    username = os.environ.get(config['username_var'])
    password = os.environ.get(config['password_var'])
    
    if not username or not password:
        print(f"❌ Missing credentials for {platform}")
        return False
    
    print(f"🧪 Testing {platform.upper()} login simulation...")
    print(f"   👤 Username: {username}")
    print(f"   🔐 Password: {'*' * len(password)}")
    
    try:
        # Import enhanced platform poster
        from enhanced_platform_poster import ENHANCED_POSTERS
        
        if platform in ENHANCED_POSTERS:
            print(f"   ✅ Enhanced 2FA poster available for {platform}")
            print(f"   🔧 Ready for live testing with Selenium + Gmail 2FA")
            return True
        else:
            print(f"   ⚠️  Enhanced poster not implemented yet for {platform}")
            print(f"   💡 Can still test basic login functionality")
            return True
            
    except Exception as e:
        print(f"   ❌ Error testing {platform}: {e}")
        return False

def create_test_workflow_script():
    """Create a script to test live 2FA workflows"""
    
    script_content = '''#!/usr/bin/env python3
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
        
        proceed = input("\\nProceed with live test? (y/N): ").lower().strip()
        
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
        print("Platforms: gsmexchange, cellpex, kadorf, hubx, handlot")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    test_live_2fa_workflow(platform)
'''
    
    script_path = backend_dir / 'test_live_2fa_workflow.py'
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Created live testing script: {script_path}")
    return script_path

def main():
    """Setup platform testing environment"""
    print("🚀 Platform Testing Setup\n")
    
    # Check local credentials
    available, missing = check_local_credentials()
    
    if available:
        print(f"✅ Found credentials for {len(available)} platform(s): {', '.join(available)}")
        
        # Test available platforms
        for platform in available[:2]:  # Test first 2 to avoid overwhelming
            test_platform_login_simulation(platform)
            print()
    
    if missing:
        print(f"⚠️  Missing credentials for {len(missing)} platform(s): {', '.join(missing)}")
    
    # Generate Railway setup
    print("\\n" + "="*60)
    generate_railway_env_setup()
    
    # Create live testing script
    print("\\n" + "="*60)
    create_test_workflow_script()
    
    print("\\n📋 Next Steps:")
    print("1. Set up missing platform credentials locally or on Railway")
    print("2. Run: python test_live_2fa_workflow.py gsmexchange")
    print("3. Test other platforms one by one")
    print("4. Deploy to Railway for production testing")

if __name__ == "__main__":
    main()