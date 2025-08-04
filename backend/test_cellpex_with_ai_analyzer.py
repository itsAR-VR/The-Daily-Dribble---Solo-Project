#!/usr/bin/env python3
"""
Cellpex with AI Analyzer - Uses GPT-4o Mini to find submit button
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from cellpex_ai_analyzer import CellpexAIAnalyzer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def run_cellpex_with_ai():
    """Use AI to analyze and submit Cellpex listing"""
    
    load_dotenv()
    
    print("🤖 CELLPEX WITH AI ANALYZER")
    print("="*50)
    print("Using GPT-4o Mini to find submit button")
    
    # Test listing
    listing_data = {
        "category": "Cell Phones",
        "brand": "Apple",
        "model": "iPhone 15 Pro Max",
        "memory": "1TB",
        "quantity": 2,
        "min_order": 1,
        "price": 1299.00,
        "condition": "New",
        "sim_lock": "Unlocked",
        "market_spec": "US Market", 
        "carrier": "",
        "packing": "Original Box",
        "incoterm": "FOB",
        "available_date": datetime.now().strftime("%m/%d/%Y"),
        "item_weight": 0.5,
        "description": "Latest iPhone 15 Pro Max 1TB. Brand new, sealed box.",
        "remarks": "Premium device, ships immediately"
    }
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        # Initialize components
        cellpex_poster = EnhancedCellpexPoster(driver)
        field_mapper = CellpexFieldMapper(driver)
        ai_analyzer = CellpexAIAnalyzer(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Verify URL
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        # Step 3: Fill form
        print("\n📍 Step 3: Filling form...")
        fill_results = field_mapper.map_and_fill_form(listing_data)
        
        success_count = sum(1 for v in fill_results.values() if v)
        print(f"✅ Filled {success_count}/{len(fill_results)} fields")
        
        # Wait for form to be ready
        time.sleep(3)
        
        # Take screenshot
        driver.save_screenshot("cellpex_ai_ready.png")
        
        # Step 4: Use AI to find and click submit
        print("\n📍 Step 4: Using AI to find submit button...")
        
        if ai_analyzer.find_and_click_submit():
            print("✅ AI found and clicked submit button!")
            
            # Wait for result
            print("\n⏳ Waiting for submission...")
            time.sleep(10)
            
            # Check result
            final_url = driver.current_url
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_screenshot = f"cellpex_ai_final_{timestamp}.png"
            driver.save_screenshot(final_screenshot)
            
            print(f"\n📍 Final URL: {final_url}")
            print(f"📸 Final screenshot: {final_screenshot}")
            
            # Check for success
            if "wholesale-search-results" in final_url:
                print("🎉 SUCCESS! Redirected to search results!")
                return True
            elif "success" in driver.page_source.lower():
                print("🎉 SUCCESS! Found success message!")
                return True
            else:
                print("📍 Check screenshot and account for result")
                
        else:
            print("❌ AI could not find submit button")
            
            # Fallback: Try direct form submission
            print("\n📍 Fallback: Trying direct form submission...")
            
            result = driver.execute_script("""
                // Find the form with listing fields
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    if (forms[i].querySelector('[name="txtBrandModel"]')) {
                        forms[i].submit();
                        return 'submitted';
                    }
                }
                return 'not_found';
            """)
            
            if result == 'submitted':
                print("📤 Form submitted directly")
                time.sleep(10)
                
                final_url = driver.current_url
                driver.save_screenshot("cellpex_fallback_result.png")
                print(f"📍 Final URL after fallback: {final_url}")
        
        # Keep open to verify
        print("\n👀 Keeping browser open for 15 seconds...")
        print("Check your Cellpex account for the listing!")
        time.sleep(15)
        
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot(f"cellpex_ai_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🤖 CELLPEX AI-POWERED SUBMIT")
    print("="*50)
    
    success = run_cellpex_with_ai()
    
    if success:
        print("\n🎉 AI-powered listing posted!")
    else:
        print("\n❌ Could not verify listing")
        print("Check screenshots and your account")
    
    sys.exit(0 if success else 1)