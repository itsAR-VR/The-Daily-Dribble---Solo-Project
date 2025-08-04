#!/usr/bin/env python3
"""
Cellpex Complete Fix - Fill ALL required fields properly
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time

def fix_cellpex_properly():
    """Actually fix Cellpex by filling ALL required fields"""
    
    load_dotenv()
    
    print("🔧 CELLPEX COMPLETE FIX")
    print("="*50)
    print("Filling ALL required fields properly")
    print("="*50)
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        # Initialize poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigate to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Fill ALL required fields based on error messages
        print("\n📍 Step 3: Filling ALL required fields...")
        
        required_fields = {
            "selCateg": {"type": "dropdown", "value": "Cell Phones", "label": "Category"},
            "selBrand": {"type": "dropdown", "value": "Apple", "label": "Brand"},
            "selCondition": {"type": "dropdown", "value": "New", "label": "Condition"},
            "selSIMlock": {"type": "dropdown", "value": "Unlocked", "label": "SIM Lock"},
            "selMarketSpec": {"type": "dropdown", "value": "US Market", "label": "Market Spec"},
            "selPacking": {"type": "dropdown", "value": "Original Box", "label": "Packing"},
            "selIncoterm": {"type": "dropdown", "value": "FOB", "label": "Incoterm"},
            "txtAvailable": {"type": "input", "value": datetime.now().strftime("%m/%d/%Y"), "label": "Available Date"},
            "txtQuantity": {"type": "input", "value": "10", "label": "Quantity"},
            "txtMinOrder": {"type": "input", "value": "1", "label": "Min Order"},
            "txtPrice": {"type": "input", "value": "799.99", "label": "Price"},
            "txtWeight": {"type": "input", "value": "0.5", "label": "Weight"},
            "txtCarrier": {"type": "input", "value": "", "label": "Carrier"},
            "txtBrandModel": {"type": "input", "value": "Apple iPhone 14 Pro", "label": "Product Name"},
            "areaComments": {"type": "textarea", "value": "Brand new iPhone 14 Pro. Factory sealed, never opened. Ships immediately.", "label": "Description"},
            "areaRemarks": {"type": "textarea", "value": "Memory: 256GB | Color: Space Black | Premium device", "label": "Remarks"}
        }
        
        filled_count = 0
        errors = []
        
        for field_name, field_info in required_fields.items():
            try:
                if field_info["type"] == "dropdown":
                    # Handle dropdown
                    select_element = Select(driver.find_element(By.NAME, field_name))
                    select_element.select_by_visible_text(field_info["value"])
                    print(f"✅ {field_info['label']}: {field_info['value']}")
                    filled_count += 1
                    
                elif field_info["type"] == "input":
                    # Handle input field
                    element = driver.find_element(By.NAME, field_name)
                    element.clear()
                    element.send_keys(field_info["value"])
                    print(f"✅ {field_info['label']}: {field_info['value']}")
                    filled_count += 1
                    
                elif field_info["type"] == "textarea":
                    # Handle textarea with JavaScript
                    element = driver.find_element(By.NAME, field_name)
                    driver.execute_script("""
                        arguments[0].value = arguments[1];
                        arguments[0].dispatchEvent(new Event('change'));
                    """, element, field_info["value"])
                    print(f"✅ {field_info['label']}: {field_info['value'][:50]}...")
                    filled_count += 1
                    
            except Exception as e:
                error_msg = f"❌ Failed to fill {field_info['label']} ({field_name}): {str(e)}"
                print(error_msg)
                errors.append(error_msg)
        
        print(f"\n📊 Filled {filled_count}/{len(required_fields)} fields")
        if errors:
            print("⚠️ Errors encountered:")
            for error in errors:
                print(f"  {error}")
        
        # Take screenshot before submit
        driver.save_screenshot("cellpex_fixed_before_submit.png")
        print("📸 Pre-submit screenshot saved")
        
        # Step 4: Find and click the correct submit button
        print("\n📍 Step 4: Finding correct submit button...")
        
        # Strategy 1: Find submit button within the form
        try:
            form = driver.find_element(By.ID, "frmSubmit")
            submit_button = form.find_element(By.CSS_SELECTOR, "input[type='submit'][value!='']")
            
            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)
            
            # Highlight button
            driver.execute_script("""
                arguments[0].style.border = '5px solid lime';
                arguments[0].style.backgroundColor = 'yellow';
            """, submit_button)
            
            print(f"✅ Found submit button: value='{submit_button.get_attribute('value')}'")
            
            # Click it
            submit_button.click()
            print("✅ Clicked submit button")
            
        except Exception as e:
            print(f"❌ Could not find/click submit button: {e}")
            
            # Fallback: Try JavaScript click
            try:
                driver.execute_script("""
                    const form = document.getElementById('frmSubmit');
                    const submitBtn = form.querySelector('input[type="submit"]:last-of-type');
                    if (submitBtn) {
                        submitBtn.click();
                        return 'clicked';
                    }
                    return 'not_found';
                """)
                print("✅ Clicked submit via JavaScript")
            except:
                print("❌ JavaScript click also failed")
        
        # Step 5: Wait and check results
        print("\n📍 Step 5: Checking submission results...")
        time.sleep(10)
        
        # Get current URL
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        # Check for errors on page
        error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .validation-error, .fv-help-block")
        if error_elements:
            print("\n⚠️ Validation errors found:")
            for err in error_elements:
                if err.text.strip():
                    print(f"  - {err.text.strip()}")
        
        # Take screenshot
        driver.save_screenshot("cellpex_fixed_after_submit.png")
        print("📸 Post-submit screenshot saved")
        
        # Check for success
        success_indicators = [
            "success" in current_url.lower(),
            "thank" in driver.page_source.lower(),
            "posted" in driver.page_source.lower(),
            "your listing" in driver.page_source.lower()
        ]
        
        if any(success_indicators):
            print("✅ Success indicators found!")
            return True
        elif "search-results" in current_url:
            print("❌ Redirected to search results - NOT SUCCESS")
            return False
        elif "list/wholesale-inventory" in current_url:
            print("⚠️ Still on form page - check for validation errors")
            return False
        else:
            print("❓ Unknown state")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot(f"cellpex_fix_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return False
        
    finally:
        if driver:
            print("\n👀 Keeping browser open for 30 seconds...")
            time.sleep(30)
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🔧 CELLPEX COMPLETE FIX")
    print("="*50)
    print("⚠️  This will attempt to properly fill ALL fields")
    print("="*50)
    
    success = fix_cellpex_properly()
    
    if success:
        print("\n✅ SUBMISSION SUCCESSFUL!")
    else:
        print("\n❌ SUBMISSION FAILED")
        print("Check screenshots for details")
    
    sys.exit(0 if success else 1)