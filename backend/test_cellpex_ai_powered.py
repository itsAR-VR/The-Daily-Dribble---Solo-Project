#!/usr/bin/env python3
"""
AI-Powered Cellpex Listing Bot
Uses GPT-4o vision to intelligently fill forms
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from intelligent_form_handler import IntelligentFormHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

def run_ai_powered_cellpex():
    """Run Cellpex listing with AI assistance"""
    
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([username, password, openai_key]):
        print("❌ Missing credentials (CELLPEX_USERNAME, CELLPEX_PASSWORD, or OPENAI_API_KEY)")
        return False
    
    print("🤖 AI-POWERED CELLPEX BOT")
    print("="*50)
    
    # User data from frontend (example)
    user_data = {
        "category": "Cell Phones",
        "brand": "Apple", 
        "model": "iPhone 14 Pro",
        "memory": "256GB",
        "quantity": 5,
        "min_order": 1,
        "price": 899.00,
        "condition": "New",
        "sim_lock": "Unlocked",
        "market_spec": "US Market",
        "carrier": "",  # Empty for unlocked
        "packing": "Original Box",
        "incoterm": "FOB",
        "delivery_days": 3,
        "item_weight": 0.5,
        "description": "Brand new iPhone 14 Pro, factory sealed, original packaging. Fast shipping available.",
        "colors": ["Space Black", "Silver", "Gold"],
        "private_notes": "Handle with care - premium device"
    }
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Initialize poster for login
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Initialize AI handler
        ai_handler = IntelligentFormHandler(driver, openai_key)
        
        # Step 1: Login with 2FA
        print("\n📍 Step 1: Login with 2FA...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed")
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(4)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Use AI to fill the form
        print("\n📍 Step 3: AI analyzing and filling form...")
        
        task = """Fill out this wholesale inventory listing form with the provided user data. 
        Make sure to:
        1. Select the correct category (Cell Phones/Smartphones)
        2. Select Apple brand
        3. Fill all required fields
        4. Select appropriate dropdowns based on the user data
        5. Fill description and remarks appropriately"""
        
        success, message = ai_handler.handle_form_intelligently(task, user_data)
        
        if success:
            print(f"✅ {message}")
            
            # Take final screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_screenshot = f"cellpex_ai_final_{timestamp}.png"
            driver.save_screenshot(final_screenshot)
            print(f"📸 Final screenshot: {final_screenshot}")
            
            # Check URL for success
            final_url = driver.current_url
            print(f"📍 Final URL: {final_url}")
            
            if "success" in final_url or "posted" in final_url:
                print("🎉 LISTING POSTED SUCCESSFULLY!")
            else:
                # If we're still on the form, check for errors
                print("\n🔍 Checking for form errors...")
                
                # Use AI to analyze any errors
                error_analysis = ai_handler.handle_unexpected_situation(
                    "Form submission might have failed. Check for validation errors."
                )
                print(f"🤖 AI Analysis: {error_analysis}")
        else:
            print(f"❌ {message}")
            
            # Let AI try to recover
            recovery = ai_handler.handle_unexpected_situation(
                f"Form filling failed: {message}"
            )
            print(f"🔧 AI Recovery suggestion: {recovery}")
        
        # Keep browser open for 10 seconds to review
        print("\n⏳ Keeping browser open for review (10 seconds)...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver and ai_handler:
            # Let AI analyze the error
            try:
                error_help = ai_handler.handle_unexpected_situation(str(e))
                print(f"\n🤖 AI Error Analysis: {error_help}")
            except:
                pass
                
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🤖 CELLPEX AI-POWERED LISTING BOT")
    print("="*50)
    print("Using GPT-4o vision to intelligently handle forms")
    print("="*50)
    
    success = run_ai_powered_cellpex()
    
    if success:
        print("\n✅ AI-powered run completed!")
    else:
        print("\n❌ AI-powered run failed!")
    
    sys.exit(0 if success else 1)