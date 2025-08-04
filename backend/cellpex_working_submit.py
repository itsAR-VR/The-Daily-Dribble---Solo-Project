#!/usr/bin/env python3
"""
Working Cellpex Submit - Actually posts the listing
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def run_working_cellpex():
    """Actually submit a working Cellpex listing"""
    
    load_dotenv()
    
    print("🎯 CELLPEX WORKING SUBMIT")
    print("="*50)
    print("This WILL post a listing!")
    
    # Real listing data
    listing_data = {
        "category": "Cell Phones",
        "brand": "Apple",
        "model": "iPhone 14 Pro",
        "memory": "256GB",
        "quantity": 5,
        "min_order": 1,
        "price": 850.00,
        "condition": "New",
        "sim_lock": "Unlocked", 
        "market_spec": "US Market",
        "carrier": "",
        "packing": "Original Box",
        "incoterm": "FOB",
        "available_date": datetime.now().strftime("%m/%d/%Y"),
        "item_weight": 0.5,
        "description": "Brand new iPhone 14 Pro 256GB. Factory sealed, original packaging.",
        "remarks": "Ships within 24 hours"
    }
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        # Initialize components
        cellpex_poster = EnhancedCellpexPoster(driver)
        field_mapper = CellpexFieldMapper(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login with 2FA...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate DIRECTLY to sell inventory
        print("\n📍 Step 2: Going DIRECTLY to Sell Inventory...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        
        # Wait for page to fully load
        time.sleep(5)
        
        # Dismiss any popups
        cellpex_poster._dismiss_popups(driver)
        
        # Verify we're on the right page
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        if "list/wholesale-inventory" not in current_url:
            print("❌ Not on listing page!")
            return False
            
        # Step 3: Fill the form
        print("\n📍 Step 3: Filling form...")
        fill_results = field_mapper.map_and_fill_form(listing_data)
        
        success_count = sum(1 for v in fill_results.values() if v)
        print(f"✅ Filled {success_count}/{len(fill_results)} fields")
        
        # Take screenshot
        driver.save_screenshot("cellpex_ready_to_submit.png")
        print("📸 Form filled screenshot saved")
        
        # Step 4: Find the ACTUAL submit button
        print("\n📍 Step 4: Finding ACTUAL submit button...")
        
        # Wait a bit for form to be ready
        time.sleep(2)
        
        # Method 1: Try to find submit button by common patterns
        submit_found = False
        
        # Common submit button selectors
        submit_selectors = [
            "input[type='submit'][value*='Save']",
            "input[type='submit'][value*='Submit']",
            "input[type='submit'][value*='Post']",
            "input[type='submit'][value*='List']",
            "button[type='submit']",
            "input[name='btnSubmit']",
            "input[name='submit']",
            "input.btn-primary[type='submit']",
            "input.submit",
            "#btnSubmit"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    print(f"✅ Found submit button: {selector}")
                    
                    # Scroll to button
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                    time.sleep(1)
                    
                    # Highlight the button
                    driver.execute_script("""
                        arguments[0].style.border = '5px solid red';
                        arguments[0].style.backgroundColor = 'yellow';
                    """, submit_btn)
                    
                    # Take screenshot before clicking
                    driver.save_screenshot("cellpex_submit_button_found.png")
                    print("📸 Submit button screenshot saved")
                    
                    # Click the button
                    try:
                        submit_btn.click()
                        submit_found = True
                        print("✅ Clicked submit button!")
                        break
                    except:
                        # Try JavaScript click
                        driver.execute_script("arguments[0].click();", submit_btn)
                        submit_found = True
                        print("✅ Clicked submit button via JavaScript!")
                        break
                        
            except:
                continue
        
        if not submit_found:
            print("\n❌ Could not find submit button with selectors")
            print("📍 Trying to submit form directly...")
            
            # Find the form and submit it
            driver.execute_script("""
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    var form = forms[i];
                    if (form.querySelector('[name="txtBrandModel"]')) {
                        console.log('Submitting listing form directly');
                        form.submit();
                        return true;
                    }
                }
                return false;
            """)
            print("📤 Form submitted directly")
        
        # Step 5: Wait and verify submission
        print("\n⏳ Waiting for submission result...")
        time.sleep(10)
        
        # Take final screenshot
        final_url = driver.current_url
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"cellpex_final_result_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        
        print(f"\n📍 Final URL: {final_url}")
        print(f"📸 Final screenshot: {final_screenshot}")
        
        # Check if we were redirected or listing was created
        if "wholesale-search-results" in final_url:
            print("✅ Redirected to search results - listing likely created!")
            return True
        elif "success" in driver.page_source.lower() or "posted" in driver.page_source.lower():
            print("🎉 SUCCESS! Listing posted!")
            return True
        elif "list/wholesale-inventory" in final_url:
            # Check for errors on the page
            page_text = driver.page_source
            if "error" in page_text.lower():
                print("❌ Form has errors")
            else:
                print("📍 Still on form page - check screenshot for result")
        else:
            print("❓ Unknown result - check final screenshot")
        
        # Keep browser open to verify
        print("\n👀 Keeping browser open for 20 seconds to verify...")
        print("Check if the listing appears in your account!")
        time.sleep(20)
        
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            error_screenshot = f"cellpex_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            
        return False
        
    finally:
        if driver:
            # Take one more screenshot before closing
            driver.save_screenshot("cellpex_final_state.png")
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🎯 CELLPEX WORKING SUBMIT")
    print("="*50)
    print("⚠️  This will create a REAL listing!")
    print("="*50)
    
    success = run_working_cellpex()
    
    if success:
        print("\n✅ Listing posted successfully!")
    else:
        print("\n❌ Could not verify listing was posted")
        print("Check screenshots and your Cellpex account")
    
    sys.exit(0 if success else 1)