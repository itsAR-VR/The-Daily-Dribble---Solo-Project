#!/usr/bin/env python3
"""
FOCUSED Cellpex Listing - Stay on listing page, take final screenshots
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

def take_final_screenshots(driver, prefix="cellpex"):
    """Take multiple screenshots of final state"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Full page screenshot
    full_screenshot = f"{prefix}_final_full_{timestamp}.png"
    driver.save_screenshot(full_screenshot)
    print(f"📸 Full page screenshot: {full_screenshot}")
    
    # Scroll to bottom and take another
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    bottom_screenshot = f"{prefix}_final_bottom_{timestamp}.png"
    driver.save_screenshot(bottom_screenshot)
    print(f"📸 Bottom screenshot: {bottom_screenshot}")
    
    # Scroll back to form area
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    return [full_screenshot, bottom_screenshot]

def run_focused_cellpex_listing():
    """Focused listing creation - stay on the listing form page"""
    
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing credentials")
        return False
    
    print("🎯 FOCUSED MODE: Creating Cellpex listing...")
    print("📍 Will stay on listing page only!")
    
    # Test data
    test_data = {
        'brand': 'Apple',
        'model': 'iPhone 14 Pro',
        'memory': '256GB',
        'quantity': 3,
        'description': 'Excellent condition iPhone 14 Pro. Factory unlocked. Original packaging.',
        'price': 850.00
    }
    
    driver = None
    screenshots = []
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Initialize poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Step 1: Login
        print("\n🔐 Step 1: Login with 2FA...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed")
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to CORRECT listing page
        print("\n📝 Step 2: Navigating to Sell Inventory page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(4)
        
        # Take screenshot of empty form
        driver.save_screenshot("cellpex_empty_form.png")
        print("📸 Empty form screenshot saved")
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Fill ONLY the listing form fields
        print("\n📋 Step 3: Filling ONLY listing form fields...")
        
        # Quantity - Use JavaScript to set value directly
        try:
            driver.execute_script("""
                var qty = document.querySelector('input[name="txtAvailable"]');
                if (qty) {
                    qty.value = arguments[0];
                    qty.dispatchEvent(new Event('change'));
                    console.log('Quantity set to: ' + arguments[0]);
                }
            """, str(test_data['quantity']))
            print(f"✅ Quantity: {test_data['quantity']}")
        except Exception as e:
            print(f"⚠️ Quantity failed: {e}")
        
        # Product name - Use JavaScript to avoid autocomplete
        try:
            product_name = f"{test_data['brand']} {test_data['model']}"
            driver.execute_script("""
                var prod = document.querySelector('input[name="txtBrandModel"]');
                if (prod) {
                    prod.value = arguments[0];
                    prod.dispatchEvent(new Event('change'));
                    console.log('Product set to: ' + arguments[0]);
                }
            """, product_name)
            print(f"✅ Product: {product_name}")
        except Exception as e:
            print(f"⚠️ Product failed: {e}")
        
        # Description
        try:
            driver.execute_script("""
                var desc = document.querySelector('textarea[name="areaComments"]');
                if (desc) {
                    desc.value = arguments[0];
                    desc.dispatchEvent(new Event('change'));
                    console.log('Description set');
                }
            """, test_data['description'])
            print("✅ Description: Set")
        except Exception as e:
            print(f"⚠️ Description failed: {e}")
        
        # Remarks with memory
        try:
            remarks = f"Memory: {test_data['memory']} | Condition: Excellent | Unlocked"
            driver.execute_script("""
                var rem = document.querySelector('textarea[name="areaRemarks"]');
                if (rem) {
                    rem.value = arguments[0];
                    rem.dispatchEvent(new Event('change'));
                    console.log('Remarks set');
                }
            """, remarks)
            print("✅ Remarks: Set with memory info")
        except Exception as e:
            print(f"⚠️ Remarks failed: {e}")
        
        # Take screenshot of filled form
        time.sleep(2)
        driver.save_screenshot("cellpex_filled_form.png")
        print("📸 Filled form screenshot saved")
        
        # Step 4: Submit ONLY to the listing form
        print("\n🚀 Step 4: Submitting listing form...")
        
        # Look for the SPECIFIC submit button for listings
        submitted = False
        
        # Strategy 1: Find the submit button in the listing form
        try:
            # Look for submit button near the form fields we just filled
            submit_btn = driver.execute_script("""
                // Find the form containing our fields
                var form = document.querySelector('form');
                if (!form) {
                    // Find form by looking for parent of our fields
                    var field = document.querySelector('input[name="txtBrandModel"]');
                    if (field) {
                        form = field.closest('form');
                    }
                }
                
                if (form) {
                    // Find submit button within this form
                    var submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
                    if (submitBtn && submitBtn.offsetParent !== null) {
                        return submitBtn;
                    }
                }
                
                // Fallback: find any visible submit button
                var allSubmits = document.querySelectorAll('input[type="submit"], button[type="submit"]');
                for (var i = 0; i < allSubmits.length; i++) {
                    if (allSubmits[i].offsetParent !== null) {
                        return allSubmits[i];
                    }
                }
                
                return null;
            """)
            
            if submit_btn:
                # Scroll to button
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                time.sleep(1)
                
                # Click it
                driver.execute_script("arguments[0].click();", submit_btn)
                print("✅ Clicked submit button!")
                submitted = True
            else:
                print("⚠️ No submit button found in form")
                
        except Exception as e:
            print(f"❌ Submit error: {e}")
        
        if not submitted:
            print("⚠️ Trying form.submit() directly...")
            try:
                driver.execute_script("""
                    var form = document.querySelector('form');
                    if (form) {
                        form.submit();
                        console.log('Form submitted directly');
                    }
                """)
                print("✅ Form.submit() called")
            except:
                print("❌ Direct submit also failed")
        
        # Wait for response
        print("\n⏳ Waiting for response...")
        time.sleep(5)
        
        # IMPORTANT: Take final screenshots before analysis
        print("\n📸 Taking final screenshots...")
        screenshots = take_final_screenshots(driver, "cellpex_listing")
        
        # Check where we ended up
        final_url = driver.current_url
        print(f"\n📍 Final URL: {final_url}")
        
        # Analyze result
        if "wholesale-inventory" in final_url and "list" in final_url:
            print("✅ Still on listing page - form may have errors")
        elif "success" in final_url or "posted" in final_url:
            print("🎉 Listing likely posted successfully!")
        elif "search" in final_url:
            print("❌ Navigated to search - wrong submission!")
        else:
            print("❓ Unknown result - check screenshots")
        
        # Auto close after 5 seconds
        print("\n🤖 Auto-closing in 5 seconds...")
        print(f"📸 Screenshots saved: {screenshots}")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            # Take error screenshots
            screenshots = take_final_screenshots(driver, "cellpex_error")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")
        
        print("\n🏁 FOCUSED RUN COMPLETE!")
        print(f"📸 Review screenshots: {screenshots}")

if __name__ == "__main__":
    print("="*50)
    print("🎯 CELLPEX FOCUSED LISTING BOT")
    print("="*50)
    
    success = run_focused_cellpex_listing()
    
    if success:
        print("\n✅ Run completed - check screenshots!")
    else:
        print("\n❌ Run failed - check error screenshots!")
    
    sys.exit(0 if success else 1)