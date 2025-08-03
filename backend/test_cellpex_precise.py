#!/usr/bin/env python3
"""
PRECISE Cellpex Listing - Target the correct form and submit button
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

def run_precise_cellpex_listing():
    """Precise listing creation - submit the RIGHT form"""
    
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing credentials")
        return False
    
    print("🎯 PRECISE MODE: Creating Cellpex listing...")
    print("🔍 Will find and submit the CORRECT form!")
    
    # Test data
    test_data = {
        'brand': 'Apple',
        'model': 'iPhone 14 Pro',
        'memory': '256GB',
        'quantity': 5,
        'description': 'Brand new condition. Factory unlocked. Fast shipping.',
        'price': 899.00
    }
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Initialize poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Step 1: Login
        print("\n🔐 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed")
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📝 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(4)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Identify the CORRECT form
        print("\n🔍 Step 3: Finding the listing form (not search form)...")
        
        # Use JavaScript to find the form that contains our listing fields
        listing_form = driver.execute_script("""
            // Find all forms
            var forms = document.querySelectorAll('form');
            console.log('Found ' + forms.length + ' forms');
            
            // Look for the form that contains listing fields
            for (var i = 0; i < forms.length; i++) {
                var form = forms[i];
                
                // Check if this form has listing fields
                var hasQuantity = form.querySelector('input[name="txtAvailable"]');
                var hasProduct = form.querySelector('input[name="txtBrandModel"]');
                var hasComments = form.querySelector('textarea[name="areaComments"]');
                
                if (hasQuantity || hasProduct || hasComments) {
                    console.log('Found listing form at index ' + i);
                    
                    // Highlight the form for debugging
                    form.style.border = '3px solid red';
                    
                    return i;  // Return the index of the listing form
                }
            }
            
            return -1;  // No listing form found
        """)
        
        if listing_form < 0:
            print("❌ Could not find listing form!")
            return False
        
        print(f"✅ Found listing form (form #{listing_form})")
        
        # Step 4: Fill the form
        print("\n📋 Step 4: Filling form fields...")
        
        # Fill fields using the specific form context
        filled_count = driver.execute_script("""
            var forms = document.querySelectorAll('form');
            var form = forms[arguments[0]];  // Get the listing form
            var count = 0;
            
            // Quantity
            var qty = form.querySelector('input[name="txtAvailable"]');
            if (qty) {
                qty.value = arguments[1];
                qty.dispatchEvent(new Event('change'));
                count++;
                console.log('Set quantity: ' + arguments[1]);
            }
            
            // Product
            var prod = form.querySelector('input[name="txtBrandModel"]');
            if (prod) {
                prod.value = arguments[2];
                prod.dispatchEvent(new Event('change'));
                count++;
                console.log('Set product: ' + arguments[2]);
            }
            
            // Description
            var desc = form.querySelector('textarea[name="areaComments"]');
            if (desc) {
                desc.value = arguments[3];
                desc.dispatchEvent(new Event('change'));
                count++;
                console.log('Set description');
            }
            
            // Remarks
            var rem = form.querySelector('textarea[name="areaRemarks"]');
            if (rem) {
                rem.value = arguments[4];
                rem.dispatchEvent(new Event('change'));
                count++;
                console.log('Set remarks');
            }
            
            return count;
        """, listing_form, 
            str(test_data['quantity']), 
            f"{test_data['brand']} {test_data['model']}",
            test_data['description'],
            f"Memory: {test_data['memory']} | Unlocked | Excellent condition")
        
        print(f"✅ Filled {filled_count} fields")
        
        # Take screenshot of filled form
        driver.save_screenshot("cellpex_precise_filled.png")
        print("📸 Filled form screenshot saved")
        
        # Step 5: Find and click the CORRECT submit button
        print("\n🎯 Step 5: Finding the correct submit button...")
        
        submit_result = driver.execute_script("""
            var forms = document.querySelectorAll('form');
            var form = forms[arguments[0]];  // Get the listing form
            
            // Find submit button WITHIN this specific form
            var submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
            
            if (submitBtn) {
                console.log('Found submit button: ' + submitBtn.outerHTML);
                
                // Highlight the button
                submitBtn.style.border = '3px solid green';
                submitBtn.style.backgroundColor = 'yellow';
                
                // Scroll to button
                submitBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                
                // Wait a bit
                setTimeout(function() {
                    // Click the button
                    submitBtn.click();
                    console.log('Clicked submit button!');
                }, 1000);
                
                return true;
            }
            
            return false;
        """, listing_form)
        
        if submit_result:
            print("✅ Found and clicked the correct submit button!")
        else:
            print("❌ Could not find submit button in listing form")
        
        # Wait for submission
        print("\n⏳ Waiting for submission result...")
        time.sleep(8)
        
        # Take final screenshots
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Full screenshot
        final_screenshot = f"cellpex_precise_final_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        print(f"📸 Final screenshot: {final_screenshot}")
        
        # Check result
        final_url = driver.current_url
        print(f"\n📍 Final URL: {final_url}")
        
        # Better result checking
        if "wholesale-inventory" in final_url and "list" in final_url:
            # Check page content for success/error messages
            page_content = driver.page_source.lower()
            
            if "success" in page_content or "posted" in page_content:
                print("🎉 SUCCESS! Listing posted!")
            elif "error" in page_content or "required" in page_content:
                print("⚠️ Form has validation errors")
                
                # Try to find error messages
                errors = driver.execute_script("""
                    var errorMsgs = document.querySelectorAll('.error, .alert, [class*="error"], [class*="alert"]');
                    var msgs = [];
                    for (var i = 0; i < errorMsgs.length; i++) {
                        if (errorMsgs[i].textContent.trim()) {
                            msgs.push(errorMsgs[i].textContent.trim());
                        }
                    }
                    return msgs;
                """)
                
                if errors:
                    print("📋 Error messages found:")
                    for err in errors:
                        print(f"  - {err}")
            else:
                print("📍 Still on listing page - check screenshot for details")
                
        elif "search" in final_url:
            print("❌ Wrong form submitted - went to search page!")
        else:
            print("❓ Unknown result - check screenshot")
        
        # Auto close
        print("\n🤖 Auto-closing in 5 seconds...")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot("cellpex_precise_error.png")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🎯 CELLPEX PRECISE LISTING BOT")
    print("="*50)
    
    success = run_precise_cellpex_listing()
    
    if success:
        print("\n✅ Precise run completed!")
    else:
        print("\n❌ Precise run failed!")
    
    sys.exit(0 if success else 1)