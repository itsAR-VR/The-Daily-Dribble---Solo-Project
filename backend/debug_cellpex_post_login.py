#!/usr/bin/env python3
"""
Debug what appears on Cellpex page after successful login
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

def debug_post_login():
    """Debug what elements are present after successful login"""
    
    # Load credentials
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        print("💡 Run: python setup_cellpex_testing.py")
        return
    
    # Create visible browser for debugging
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920x1080")
    # Keep browser visible for debugging
    
    print("🌐 Opening Chrome browser...")
    driver = webdriver.Chrome(options=options)
    
    try:
        print("📍 Navigating to Cellpex login page...")
        driver.get("https://www.cellpex.com/login")
        wait = WebDriverWait(driver, 20)
        
        print("🔐 Performing login...")
        
        # Fill username
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "txtUser")))
        user_field.clear()
        user_field.send_keys(username)
        print(f"   ✅ Username entered: {username}")
        
        # Fill password  
        pass_field = wait.until(EC.presence_of_element_located((By.NAME, "txtPass")))
        pass_field.clear()
        pass_field.send_keys(password)
        print(f"   ✅ Password entered: {'*' * len(password)}")
        
        # Submit login
        submit = wait.until(EC.element_to_be_clickable((By.NAME, "btnLogin")))
        submit.click()
        print("   ✅ Login form submitted")
        
        # Wait for page to load after login
        print("⏳ Waiting for page to load after login...")
        time.sleep(5)
        
        print(f"📄 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        # Check for common success indicators
        success_indicators = [
            ("logout", "logout link"),
            ("sign out", "sign out link"), 
            ("account", "account link"),
            ("dashboard", "dashboard link"),
            ("profile", "profile link"),
            ("my account", "my account text"),
            ("welcome", "welcome message"),
            ("user", "user indicator")
        ]
        
        print("\n🔍 Looking for login success indicators...")
        found_indicators = []
        
        for text, description in success_indicators:
            try:
                elements = driver.find_elements(By.PARTIAL_LINK_TEXT, text)
                if elements:
                    found_indicators.append((text, description, "link"))
                    print(f"   ✅ Found {description}: {len(elements)} element(s)")
                    for i, elem in enumerate(elements):
                        print(f"      {i+1}. Text: '{elem.text}', Href: {elem.get_attribute('href')}")
                else:
                    # Also check in page text
                    if text.lower() in driver.page_source.lower():
                        found_indicators.append((text, description, "text"))
                        print(f"   ⚠️  Found '{text}' in page source but not as link")
            except Exception as e:
                print(f"   ❌ Error checking {description}: {e}")
        
        if not found_indicators:
            print("   ⚠️  No standard success indicators found")
        
        # Look for any navigation links
        print("\n🔍 Looking for navigation links...")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        nav_links = []
        
        for link in all_links[:20]:  # Check first 20 links
            text = link.text.strip()
            href = link.get_attribute("href")
            if text and len(text) < 50:  # Skip very long text
                nav_links.append((text, href))
                print(f"   🔗 '{text}' -> {href}")
        
        # Check URL for redirection patterns
        print(f"\n🔍 URL Analysis:")
        if "login" in driver.current_url.lower():
            print("   ⚠️  Still on login page - login might have failed")
        elif "dashboard" in driver.current_url.lower():
            print("   ✅ Redirected to dashboard - login likely successful")
        elif "account" in driver.current_url.lower():
            print("   ✅ Redirected to account page - login likely successful")
        elif driver.current_url != "https://www.cellpex.com/login":
            print(f"   ✅ Redirected away from login page - login likely successful")
            
        # Check for error messages
        print("\n🔍 Looking for error messages...")
        error_indicators = ["error", "invalid", "incorrect", "failed", "denied"]
        
        for error_text in error_indicators:
            if error_text in driver.page_source.lower():
                print(f"   ⚠️  Found '{error_text}' in page - possible error")
                
        # Look for user-specific content
        print(f"\n🔍 Looking for user-specific content...")
        if username.lower() in driver.page_source.lower():
            print(f"   ✅ Found username '{username}' in page content")
        
        # Manual inspection
        print(f"\n🔍 Browser left open for manual inspection...")
        print(f"📋 Manual checks:")
        print(f"   1. Are you logged in successfully?")
        print(f"   2. What navigation options are available?")
        print(f"   3. Is there a way to access account/profile?")
        print(f"   4. What unique elements appear when logged in?")
        
        input("Press Enter when done inspecting...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("🔒 Browser closed")

if __name__ == "__main__":
    debug_post_login()