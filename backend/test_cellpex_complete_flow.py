#!/usr/bin/env python3
"""
Test complete Cellpex flow with working 2FA email extraction
"""

import os
import time
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from gmail_service import gmail_service

def extract_code_from_cellpex_email():
    """Extract the latest Cellpex verification code"""
    if not gmail_service or not gmail_service.is_available():
        print("❌ Gmail service not available")
        return None
    
    try:
        # Simple query that we know works
        query = 'from:cellpex.com after:2025/08/03'
        print(f"🔍 Searching Gmail with query: {query}")
        
        results = gmail_service.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=5
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            print("❌ No Cellpex emails found")
            return None
        
        # Get the latest message
        msg_id = messages[0]['id']
        msg_data = gmail_service.service.users().messages().get(
            userId='me',
            id=msg_id
        ).execute()
        
        # Extract code from snippet (we know this works from our test)
        snippet = msg_data.get('snippet', '')
        codes = re.findall(r'\b(\d{6})\b', snippet)
        
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

def test_cellpex_2fa_flow():
    """Test complete Cellpex flow with 2FA"""
    
    # Load credentials
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"🚀 Testing Complete Cellpex 2FA Flow...")
    print(f"   Username: {username}")
    
    # Create driver
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920x1080")
    # Keep visible for debugging
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Step 1: Login
        print("\n📍 Step 1: Login to Cellpex...")
        driver.get("https://www.cellpex.com/login")
        
        # Fill login form
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "txtUser")))
        user_field.clear()
        user_field.send_keys(username)
        
        pass_field = wait.until(EC.presence_of_element_located((By.NAME, "txtPass")))
        pass_field.clear()
        pass_field.send_keys(password)
        
        submit = wait.until(EC.element_to_be_clickable((By.NAME, "btnLogin")))
        submit.click()
        
        print("✅ Login form submitted")
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if we're on verification page
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        if "login_verify" in current_url:
            print("✅ 2FA page detected!")
            
            # Step 2: Wait a bit for email to arrive
            print("\n📍 Step 2: Waiting for 2FA email...")
            print("⏳ Waiting 10 seconds for email delivery...")
            time.sleep(10)
            
            # Step 3: Get verification code
            print("\n📍 Step 3: Extracting verification code from email...")
            code = extract_code_from_cellpex_email()
            
            if not code:
                print("❌ Could not extract verification code")
                return False
            
            # Step 4: Enter verification code
            print(f"\n📍 Step 4: Entering verification code: {code}")
            
            # Find the code input field
            code_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[name*='code'], input[name*='verify']")
            
            if code_inputs:
                # Try the first suitable input
                code_input = code_inputs[0]
                code_input.clear()
                code_input.send_keys(code)
                print("✅ Code entered")
                
                # Find and click submit button
                submit_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                
                if submit_buttons:
                    submit_buttons[0].click()
                    print("✅ Verification submitted")
                else:
                    # Try pressing Enter
                    code_input.send_keys("\n")
                    print("✅ Verification submitted (Enter key)")
                
                # Wait for redirect
                time.sleep(5)
                
                # Check if login successful
                final_url = driver.current_url
                print(f"\n📍 Final URL: {final_url}")
                
                if "login" not in final_url:
                    print("🎉 Login successful! Navigated away from login page")
                    
                    # Take screenshot of successful login
                    driver.save_screenshot("cellpex_login_success.png")
                    print("📸 Screenshot saved: cellpex_login_success.png")
                    
                    # Try to find listing page
                    print("\n📍 Looking for listing functionality...")
                    
                    # Look for sell/post links
                    sell_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Sell")
                    post_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Post")
                    add_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Add")
                    
                    if sell_links:
                        print(f"✅ Found 'Sell' link: {sell_links[0].get_attribute('href')}")
                    if post_links:
                        print(f"✅ Found 'Post' link: {post_links[0].get_attribute('href')}")
                    if add_links:
                        print(f"✅ Found 'Add' link: {add_links[0].get_attribute('href')}")
                    
                    return True
                else:
                    print("❌ Still on login page - verification may have failed")
                    return False
            else:
                print("❌ Could not find verification code input field")
                return False
        else:
            print("❌ Not redirected to 2FA page - check if already logged in or login failed")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("cellpex_error.png")
        return False
    finally:
        print("\n🔍 Browser left open for inspection...")
        input("Press Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    test_cellpex_2fa_flow()