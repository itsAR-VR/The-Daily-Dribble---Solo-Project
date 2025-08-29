#!/usr/bin/env python3
"""
Test GSM Exchange 2FA Flow
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from gmail_service import gmail_service

def extract_gsm_2fa_code():
    """Extract GSM Exchange verification code"""
    if not gmail_service or not gmail_service.is_available():
        print("❌ Gmail service not available")
        return None
    
    try:
        # Search for GSM Exchange emails
        query = 'from:gsmexchange.com after:2025/08/03'
        print(f"🔍 Searching Gmail with query: {query}")
        
        results = gmail_service.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=5
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            print("❌ No GSM Exchange emails found")
            return None
        
        # Get the latest message
        msg_id = messages[0]['id']
        msg_data = gmail_service.service.users().messages().get(
            userId='me',
            id=msg_id
        ).execute()
        
        # Extract code from snippet
        snippet = msg_data.get('snippet', '')
        import re
        codes = re.findall(r'\b(\d{4,6})\b', snippet)  # 4-6 digit codes
        
        if codes:
            code = codes[0]
            print(f"✅ Found verification code: {code}")
            return code
        else:
            print("❌ No code found in email")
            return None
            
    except Exception as e:
        print(f"❌ Error extracting code: {e}")
        return None

def test_gsm_2fa_flow():
    """Test GSM Exchange 2FA flow"""
    
    # Load credentials
    load_dotenv()
    username = os.getenv("GSMEXCHANGE_USERNAME")
    password = os.getenv("GSMEXCHANGE_PASSWORD")
    
    if not username or not password:
        print("❌ Missing GSM Exchange credentials!")
        print("   Set GSMEXCHANGE_USERNAME and GSMEXCHANGE_PASSWORD")
        return False
    
    print(f"🚀 Testing GSM Exchange 2FA Flow...")
    print(f"   Username: {username}")
    
    # Create driver
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920x1080")
    # Keep visible for debugging
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Step 1: Navigate to login
        print("\n📍 Step 1: Navigate to GSM Exchange login...")
        driver.get("https://www.gsmexchange.com/signin")
        time.sleep(3)
        
        # Step 2: Fill login form
        print("\n📍 Step 2: Fill login form...")
        
        # Look for username/email field
        username_selectors = [
            "input[name='email']",
            "input[name='username']",
            "input[type='email']",
            "input[placeholder*='email']",
            "input[placeholder*='username']",
            "#email",
            "#username"
        ]
        
        username_field = None
        for selector in username_selectors:
            try:
                username_field = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found username field: {selector}")
                break
            except:
                continue
        
        if not username_field:
            print("❌ Could not find username field")
            driver.save_screenshot("gsm_login_page.png")
            return False
        
        username_field.clear()
        username_field.send_keys(username)
        print("✅ Username entered")
        
        # Look for password field
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "#password"
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found password field: {selector}")
                break
            except:
                continue
        
        if not password_field:
            print("❌ Could not find password field")
            driver.save_screenshot("gsm_login_page.png")
            return False
        
        password_field.clear()
        password_field.send_keys(password)
        print("✅ Password entered")
        
        # Look for submit button
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            
            "[onclick*='login']",
            "[onclick*='signin']"
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
                submit_btn.click()
                submitted = True
                print(f"✅ Form submitted using: {selector}")
                break
            except:
                continue
        
        if not submitted:
            # Try Enter key as fallback
            password_field.send_keys("\n")
            print("✅ Form submitted using Enter key")
        
        # Step 3: Check for 2FA or success
        print("\n📍 Step 3: Checking login result...")
        time.sleep(5)
        
        current_url = driver.current_url
        page_text = driver.page_source.lower()
        
        print(f"📍 Current URL: {current_url}")
        
        # Check for 2FA indicators
        tfa_indicators = [
            "verification",
            "2fa",
            "two-factor",
            "authentication code",
            "verify your identity", 
            "enter code",
            "security code",
            "phone verification",
            "sms code"
        ]
        
        needs_2fa = any(indicator in page_text for indicator in tfa_indicators)
        
        if needs_2fa:
            print("✅ 2FA required for GSM Exchange!")
            
            # Take screenshot for analysis
            driver.save_screenshot("gsm_2fa_page.png")
            print("📸 2FA page screenshot: gsm_2fa_page.png")
            
            # Step 4: Wait for 2FA email
            print("\n📍 Step 4: Waiting for 2FA email...")
            time.sleep(15)  # Wait for email
            
            # Step 5: Extract code
            print("\n📍 Step 5: Extracting verification code...")
            code = extract_gsm_2fa_code()
            
            if code:
                print(f"✅ Found 2FA code: {code}")
                
                # Step 6: Enter code
                print(f"\n📍 Step 6: Entering 2FA code: {code}")
                
                # Look for 2FA input field
                tfa_selectors = [
                    "input[name='code']",
                    "input[name='otp']",
                    "input[name='token']",
                    "input[name='verification']",
                    "input[name='verification_code']",
                    "input[placeholder*='code']",
                    "input[placeholder*='verification']",
                    "input[type='text'][maxlength='6']",
                    "input[type='text'][maxlength='4']",
                    "input[type='number']"
                ]
                
                code_field = None
                for selector in tfa_selectors:
                    try:
                        code_field = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"✅ Found 2FA field: {selector}")
                        break
                    except:
                        continue
                
                if code_field:
                    code_field.clear()
                    code_field.send_keys(code)
                    print("✅ Code entered")
                    
                    # Submit
                    submit_selectors = [
                        "button[type='submit']",
                        "input[type='submit']",
                        
                    ]
                    
                    submitted = False
                    for selector in submit_selectors:
                        try:
                            submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
                            submit_btn.click()
                            submitted = True
                            print("✅ 2FA form submitted")
                            break
                        except:
                            continue
                    
                    if not submitted:
                        code_field.send_keys("\n")
                        print("✅ 2FA submitted with Enter")
                    
                    # Wait and check result
                    time.sleep(5)
                    final_url = driver.current_url
                    print(f"📍 Final URL: {final_url}")
                    
                    if "login" not in final_url and "signin" not in final_url and "verify" not in final_url:
                        print("🎉 GSM Exchange 2FA login successful!")
                        driver.save_screenshot("gsm_success.png")
                        return True
                    else:
                        print("❌ Still on login/verify page")
                        driver.save_screenshot("gsm_still_verify.png")
                        return False
                else:
                    print("❌ Could not find 2FA input field")
                    return False
            else:
                print("❌ Could not extract 2FA code")
                return False
        else:
            print("✅ No 2FA required - login successful!")
            if "login" not in current_url and "signin" not in current_url:
                print("🎉 GSM Exchange login successful!")
                driver.save_screenshot("gsm_success_no_2fa.png")
                return True
            else:
                print("❌ Login failed - still on login page")
                driver.save_screenshot("gsm_login_failed.png")
                return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("gsm_error.png")
        return False
    finally:
        print("\n🔍 Keeping browser open for inspection...")
        input("Press Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    test_gsm_2fa_flow()