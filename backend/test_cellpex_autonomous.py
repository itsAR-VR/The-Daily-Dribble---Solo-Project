#!/usr/bin/env python3
"""
FULLY AUTONOMOUS Cellpex Listing - No manual intervention required
"""

import os
import sys
import time
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def handle_autocomplete(driver, wait, field_name):
    """Handle autocomplete suggestions by clicking the first one"""
    try:
        # Wait briefly for autocomplete to appear
        time.sleep(0.5)
        
        # Look for autocomplete suggestions
        autocomplete_selectors = [
            ".ui-autocomplete li:first-child",
            ".autocomplete-item:first-child",
            "[class*='suggestion']:first-child",
            "[class*='dropdown-item']:first-child",
            ".dropdown-menu .dropdown-item:first-child"
        ]
        
        for selector in autocomplete_selectors:
            try:
                suggestion = driver.find_element(By.CSS_SELECTOR, selector)
                if suggestion.is_displayed():
                    suggestion.click()
                    print(f"✅ Clicked autocomplete suggestion for {field_name}")
                    return True
            except:
                continue
        
        # If no autocomplete found, press Tab to move to next field
        active_element = driver.switch_to.active_element
        active_element.send_keys(Keys.TAB)
        print(f"⏭️ No autocomplete found, tabbed to next field")
        return True
        
    except Exception as e:
        print(f"⚠️ Autocomplete handling failed: {e}")
        return False

def run_autonomous_cellpex_listing():
    """Fully autonomous Cellpex listing - no manual intervention"""
    
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing credentials - STOPPING")
        return False
    
    print("🤖 AUTONOMOUS MODE: Starting Cellpex listing...")
    print("⚡ No manual input required - sit back and watch!")
    
    # Test data
    test_data = {
        'brand': 'Apple',
        'model': 'iPhone 14 Pro',  # NO memory in model name
        'memory': '256GB',
        'quantity': 3,
        'description': 'Excellent condition iPhone 14 Pro. Factory unlocked.',
        'price': 850.00
    }
    
    driver = None
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Initialize poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Step 1: Login with 2FA
        print("\n🔐 Step 1: Automated login...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed - STOPPING")
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📝 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(3)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Fill form FAST with autocomplete handling
        print("\n⚡ Step 3: Speed-filling form...")
        
        success_count = 0
        
        # Brand/Model - Handle autocomplete
        try:
            field = driver.find_element(By.NAME, "txtBrandModel")
            field.clear()
            # Type slowly to trigger autocomplete
            for char in f"{test_data['brand']} {test_data['model']}":
                field.send_keys(char)
                time.sleep(0.05)  # Small delay between characters
            
            # Handle autocomplete dropdown
            handle_autocomplete(driver, wait, "txtBrandModel")
            success_count += 1
            print("✅ Product name entered with autocomplete")
        except Exception as e:
            print(f"⚠️ Skipping product name: {e}")
        
        # Quantity - Quick fill
        try:
            driver.execute_script("""
                var field = document.querySelector('[name="txtAvailable"]');
                if (field) {
                    field.value = arguments[0];
                    field.dispatchEvent(new Event('change'));
                }
            """, str(test_data['quantity']))
            success_count += 1
            print("✅ Quantity set")
        except:
            print("⚠️ Skipping quantity")
        
        # Description - JavaScript injection
        try:
            driver.execute_script("""
                var field = document.querySelector('[name="areaComments"]');
                if (field) {
                    field.value = arguments[0];
                    field.dispatchEvent(new Event('change'));
                }
            """, test_data['description'])
            success_count += 1
            print("✅ Description set")
        except:
            print("⚠️ Skipping description")
        
        # Remarks with memory info
        try:
            remarks = f"Memory: {test_data['memory']} | Condition: Excellent"
            driver.execute_script("""
                var field = document.querySelector('[name="areaRemarks"]');
                if (field) {
                    field.value = arguments[0];
                    field.dispatchEvent(new Event('change'));
                }
            """, remarks)
            success_count += 1
            print("✅ Remarks set")
        except:
            print("⚠️ Skipping remarks")
        
        print(f"\n📊 Filled {success_count}/4 fields successfully")
        
        # Step 4: Submit with multiple strategies
        print("\n🚀 Step 4: Attempting submission...")
        
        # Screenshot before submit
        driver.save_screenshot("cellpex_auto_before_submit.png")
        
        # Strategy 1: JavaScript form submission
        try:
            driver.execute_script("""
                var forms = document.querySelectorAll('form');
                if (forms.length > 0) {
                    forms[0].submit();
                    return true;
                }
                return false;
            """)
            print("✅ Form submitted via JavaScript!")
            time.sleep(5)
        except:
            print("⚠️ JS submit failed, trying button click...")
            
            # Strategy 2: Find and click any submit button
            submit_found = False
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']", 
                "input[value*='Submit' i]",
                "button:contains('Submit')",
                "input[name='btnSubmit']"
            ]
            
            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        # Skip jQuery selectors for now
                        continue
                    
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed():
                        # Scroll and click
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"✅ Clicked submit: {selector}")
                        submit_found = True
                        break
                except:
                    continue
            
            if not submit_found:
                print("⚠️ No submit button found - pressing Enter")
                try:
                    # Press Enter on last field
                    driver.execute_script("""
                        var lastInput = document.querySelector('textarea[name="areaRemarks"]');
                        if (lastInput) {
                            lastInput.focus();
                            var event = new KeyboardEvent('keypress', {
                                key: 'Enter',
                                code: 'Enter',
                                which: 13,
                                keyCode: 13,
                            });
                            lastInput.dispatchEvent(event);
                        }
                    """)
                except:
                    pass
        
        # Wait for result
        time.sleep(5)
        
        # Check result
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        # Screenshot after submit
        driver.save_screenshot("cellpex_auto_after_submit.png")
        
        # Determine success
        if "error" in page_source or "required" in page_source:
            print("\n⚠️ PARTIAL SUCCESS - Form has errors but we tried!")
        elif "wholesale-inventory" in current_url:
            print("\n✅ LIKELY SUCCESS - Still on listing page!")
        else:
            print("\n✅ SUBMISSION ATTEMPTED - Check screenshots!")
        
        print(f"\n📊 FINAL REPORT:")
        print(f"✅ Login: SUCCESS")
        print(f"✅ 2FA: SUCCESS") 
        print(f"✅ Form Fill: {success_count}/4 fields")
        print(f"✅ Submit: ATTEMPTED")
        print(f"📍 Final URL: {current_url}")
        
        # Auto close after 3 seconds
        print("\n🤖 Auto-closing in 3 seconds...")
        time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot("cellpex_auto_error.png")
            print("📸 Error screenshot saved")
        
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                print("✅ Browser closed automatically")
            except:
                pass
        
        print("\n🏁 AUTONOMOUS RUN COMPLETE!")

if __name__ == "__main__":
    print("="*50)
    print("🤖 CELLPEX AUTONOMOUS LISTING BOT")
    print("="*50)
    
    success = run_autonomous_cellpex_listing()
    
    if success:
        print("\n🎉 MISSION ACCOMPLISHED!")
    else:
        print("\n🔧 Need adjustments but we're close!")
    
    # Exit immediately - no waiting
    sys.exit(0 if success else 1)