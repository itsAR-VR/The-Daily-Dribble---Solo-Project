#!/usr/bin/env python3
"""
Test Cellpex 2FA with CORRECT form field targeting
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
        # Simple query that works
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
        
        # Extract code from snippet
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

def test_cellpex_2fa_flow_fixed():
    """Test Cellpex 2FA with CORRECT field targeting"""
    
    # Load credentials
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"🚀 Testing Fixed Cellpex 2FA Flow...")
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
        time.sleep(3)
        
        # Check if we're on verification page
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        if "login_verify" in current_url:
            print("✅ 2FA page detected!")
            
            # Step 2: Wait for email
            print("\n📍 Step 2: Waiting for 2FA email...")
            time.sleep(10)
            
            # Step 3: Get verification code
            print("\n📍 Step 3: Extracting verification code from email...")
            code = extract_code_from_cellpex_email()
            
            if not code:
                print("❌ Could not extract verification code")
                return False
            
            # Step 4: Enter verification code in CORRECT field
            print(f"\n📍 Step 4: Entering verification code in CORRECT field: {code}")
            
            # Look for the 2FA form specifically - NOT the search bar
            print("🔍 Looking for 2FA form fields...")
            
            # Method 1: Look for forms containing "Access Code" or similar text
            try:
                # Wait for the access code form to be present
                access_code_text = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Access Code Required')]")
                ))
                print("✅ Found 'Access Code Required' text")
                
                # Find input field near this text (likely in same form)
                # Look for input fields in the form context, not the header search
                possible_selectors = [
                    "//form//input[@type='text']",  # Text input in a form
                    "//form//input[not(@type)]",    # Input without type in a form
                    "//input[@name='access_code']", # Common name
                    "//input[@name='code']",        # Simple name
                    "//input[@name='verification_code']", # Full name
                    "//input[@placeholder*='code']",      # Placeholder hint
                    "//input[@maxlength='6']",             # 6-digit code
                    "//div[contains(text(), 'Access Code')]//following::input[1]", # Input after "Access Code" text
                    "//form[.//text()[contains(., 'Access Code')]]//input[@type='text']" # Text input in form with "Access Code"
                ]
                
                code_input = None
                for selector in possible_selectors:
                    try:
                        potential_inputs = driver.find_elements(By.XPATH, selector)
                        for inp in potential_inputs:
                            # Skip if it's the search bar (likely has certain classes or IDs)
                            input_class = inp.get_attribute("class") or ""
                            input_id = inp.get_attribute("id") or ""
                            input_name = inp.get_attribute("name") or ""
                            
                            # Skip search-related inputs
                            if any(term in (input_class + input_id + input_name).lower() for term in ['search', 'query', 'find']):
                                continue
                            
                            # This looks like our 2FA input
                            code_input = inp
                            print(f"✅ Found 2FA input field using selector: {selector}")
                            print(f"   - Class: {input_class}")
                            print(f"   - ID: {input_id}")
                            print(f"   - Name: {input_name}")
                            break
                        
                        if code_input:
                            break
                    except:
                        continue
                
                if not code_input:
                    print("❌ Could not find 2FA input field")
                    # Take screenshot for debugging
                    driver.save_screenshot("cellpex_2fa_form_debug.png")
                    print("📸 Debug screenshot saved: cellpex_2fa_form_debug.png")
                    return False
                
                # Clear and enter the code
                code_input.clear()
                time.sleep(1)
                code_input.send_keys(code)
                print(f"✅ Code entered in correct field: {code}")
                
                # Step 5: Submit the form
                print("\n📍 Step 5: Submitting 2FA form...")
                
                # Find submit button using simple selectors (no :contains)
                submit_selectors = [
                    "//form//button[@type='submit']",
                    "//form//input[@type='submit']",
                    "//button[contains(text(), 'Submit')]",
                    "//button[contains(text(), 'Verify')]",
                    "//input[@value='Submit']",
                    "//input[@value='Verify']"
                ]
                
                submitted = False
                for selector in submit_selectors:
                    try:
                        submit_btn = driver.find_element(By.XPATH, selector)
                        submit_btn.click()
                        submitted = True
                        print(f"✅ Form submitted using: {selector}")
                        break
                    except:
                        continue
                
                if not submitted:
                    # Try Enter key as fallback
                    code_input.send_keys("\n")
                    print("✅ Form submitted using Enter key")
                
                # Wait for redirect
                time.sleep(5)
                
                # Check if login successful
                final_url = driver.current_url
                print(f"\n📍 Final URL: {final_url}")
                
                if "login" not in final_url and "verify" not in final_url:
                    print("🎉 SUCCESS! Cellpex 2FA login completed!")
                    
                    # Take success screenshot
                    driver.save_screenshot("cellpex_2fa_success.png")
                    print("📸 Success screenshot saved: cellpex_2fa_success.png")
                    
                    # Look for listing functionality
                    print("\n📍 Step 6: Looking for listing functionality...")
                    
                    # Check current page for navigation
                    page_text = driver.page_source
                    if "Sell Inventory" in page_text:
                        print("✅ Found 'Sell Inventory' option")
                    if "My Inventory" in page_text:
                        print("✅ Found 'My Inventory' option")
                    if "Add" in page_text and "Product" in page_text:
                        print("✅ Found product/listing options")
                    
                    return True
                else:
                    print("❌ Still on verification page - code may be incorrect or expired")
                    driver.save_screenshot("cellpex_2fa_still_verify.png")
                    return False
                    
            except TimeoutException:
                print("❌ Could not find 'Access Code Required' text")
                driver.save_screenshot("cellpex_no_access_code_text.png")
                return False
        else:
            print("❌ Not redirected to 2FA page")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("cellpex_2fa_error.png")
        return False
    finally:
        print("\n🔍 Keeping browser open for inspection...")
        input("Press Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    test_cellpex_2fa_flow_fixed()