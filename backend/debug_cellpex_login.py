#!/usr/bin/env python3
"""
Debug Cellpex login page structure
"""

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import time

def debug_cellpex_login():
    """Debug the Cellpex login page to see available form elements"""
    
    # Create driver with visible browser for debugging
    options = webdriver.ChromeOptions()
    # Remove headless mode so we can see what's happening
    # options.add_argument("--headless")
    options.add_argument("--window-size=1920x1080")
    
    print("🌐 Opening Chrome browser (visible for debugging)...")
    driver = webdriver.Chrome(options=options)
    
    try:
        print("📍 Navigating to Cellpex login page...")
        driver.get("https://www.cellpex.com/login")
        
        # Wait for page to load
        print("⏳ Waiting for page to load...")
        time.sleep(5)
        
        print(f"📄 Page title: {driver.title}")
        print(f"🔗 Current URL: {driver.current_url}")
        
        # Try to find any input fields
        print("\n🔍 Looking for input fields...")
        
        input_fields = driver.find_elements(By.TAG_NAME, "input")
        print(f"📊 Found {len(input_fields)} input fields:")
        
        for i, field in enumerate(input_fields):
            field_type = field.get_attribute("type") or "text"
            field_name = field.get_attribute("name") or "no-name"
            field_id = field.get_attribute("id") or "no-id"
            field_placeholder = field.get_attribute("placeholder") or "no-placeholder"
            field_class = field.get_attribute("class") or "no-class"
            
            print(f"  {i+1}. Type: {field_type}, Name: {field_name}, ID: {field_id}")
            print(f"     Placeholder: {field_placeholder}")
            print(f"     Class: {field_class}")
            print()
        
        # Look for form elements
        print("🔍 Looking for forms...")
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"📊 Found {len(forms)} forms")
        
        # Look for buttons
        print("🔍 Looking for buttons...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"📊 Found {len(buttons)} buttons:")
        
        for i, button in enumerate(buttons):
            button_text = button.text or "no-text"
            button_type = button.get_attribute("type") or "button"
            button_class = button.get_attribute("class") or "no-class"
            
            print(f"  {i+1}. Text: '{button_text}', Type: {button_type}")
            print(f"     Class: {button_class}")
            print()
        
        # Check if we're redirected or if login form is loaded
        if "login" not in driver.current_url.lower():
            print("⚠️  Redirected away from login page!")
            print(f"   New URL: {driver.current_url}")
        
        # Keep browser open for manual inspection
        print("\n🔍 Browser is open for manual inspection...")
        print("📋 Manual checks:")
        print("   1. Is the login form visible?")
        print("   2. What are the actual field names/IDs?") 
        print("   3. Are there any CAPTCHAs or bot detection?")
        print("   4. Does the page require JavaScript?")
        
        input("Press Enter to close browser and continue...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("🔒 Browser closed")

if __name__ == "__main__":
    debug_cellpex_login()