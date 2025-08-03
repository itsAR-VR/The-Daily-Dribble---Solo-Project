#!/usr/bin/env python3
"""
Fixed Cellpex Listing Flow - Handles form field interaction issues
"""

import os
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from gmail_service import gmail_service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def enhanced_form_interaction(driver, field_name, value, field_type="input"):
    """Enhanced form field interaction with multiple fallback strategies"""
    try:
        print(f"🔧 Interacting with {field_name}...")
        
        # Strategy 1: Standard interaction
        try:
            if field_type == "textarea":
                element = driver.find_element(By.NAME, field_name)
            else:
                element = driver.find_element(By.NAME, field_name)
            
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Click to focus
            element.click()
            time.sleep(0.5)
            
            # Clear and enter value
            element.clear()
            element.send_keys(value)
            
            print(f"✅ {field_name} filled successfully")
            return True
            
        except Exception as e:
            print(f"⚠️  Standard method failed for {field_name}: {e}")
        
        # Strategy 2: ActionChains
        try:
            element = driver.find_element(By.NAME, field_name)
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            time.sleep(0.5)
            
            # Clear with Ctrl+A and Delete
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            element.send_keys(value)
            
            print(f"✅ {field_name} filled with ActionChains")
            return True
            
        except Exception as e:
            print(f"⚠️  ActionChains method failed for {field_name}: {e}")
        
        # Strategy 3: JavaScript injection
        try:
            element = driver.find_element(By.NAME, field_name)
            driver.execute_script(f"arguments[0].value = '{value}';", element)
            # Trigger change event
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", element)
            
            print(f"✅ {field_name} filled with JavaScript")
            return True
            
        except Exception as e:
            print(f"⚠️  JavaScript method failed for {field_name}: {e}")
        
        # Strategy 4: Try alternative selectors
        try:
            selectors = [
                f"#{field_name}",
                f"[id='{field_name}']",
                f"[name='{field_name}']",
                f"textarea[name='{field_name}']",
                f"input[name='{field_name}']"
            ]
            
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                    element.clear()
                    element.send_keys(value)
                    print(f"✅ {field_name} filled with selector: {selector}")
                    return True
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Alternative selectors failed for {field_name}: {e}")
        
        print(f"❌ All methods failed for {field_name}")
        return False
        
    except Exception as e:
        print(f"❌ Error in enhanced_form_interaction for {field_name}: {e}")
        return False

def find_submit_button(driver):
    """Enhanced submit button finding with multiple strategies"""
    print("🔍 Looking for submit button...")
    
    # Strategy 1: Common submit selectors
    submit_selectors = [
        "button[type='submit']",
        "input[type='submit']",
        "button[value*='Save']",
        "button[value*='Submit']",
        "input[value*='Save']",
        "input[value*='Submit']",
        "[onclick*='submit']",
        "[onclick*='save']"
    ]
    
    for selector in submit_selectors:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    print(f"✅ Found submit button: {selector}")
                    return button
        except:
            continue
    
    # Strategy 2: Text-based search
    text_selectors = [
        "//button[contains(text(), 'Save')]",
        "//button[contains(text(), 'Submit')]", 
        "//button[contains(text(), 'Post')]",
        "//button[contains(text(), 'Add')]",
        "//button[contains(text(), 'Create')]",
        "//input[@value='Save']",
        "//input[@value='Submit']",
        "//input[@value='Post']"
    ]
    
    for selector in text_selectors:
        try:
            buttons = driver.find_elements(By.XPATH, selector)
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    print(f"✅ Found submit button: {selector}")
                    return button
        except:
            continue
    
    # Strategy 3: Look for any clickable button in forms
    try:
        form_buttons = driver.find_elements(By.CSS_SELECTOR, "form button, form input[type='button']")
        for button in form_buttons:
            if button.is_displayed() and button.is_enabled():
                print(f"✅ Found form button: {button.get_attribute('outerHTML')[:100]}...")
                return button
    except:
        pass
    
    print("❌ No submit button found")
    return None

def test_cellpex_fixed_listing():
    """Test Cellpex with fixed form interaction"""
    
    # Load environment variables
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"🚀 Testing FIXED Cellpex Listing Flow...")
    print(f"   Username: {username}")
    
    # Test data
    test_data = {
        'brand': 'Apple',
        'model': 'iPhone 15 Pro',
        'memory': '128GB',
        'condition': 'Excellent',
        'quantity': 5,
        'price': 899.00,
        'description': 'Brand new iPhone 15 Pro in pristine condition. Factory unlocked.',
        'color': 'Natural Titanium'
    }
    
    try:
        # Initialize browser
        print("\n📍 Step 1: Initializing browser...")
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        
        # Initialize poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        wait = WebDriverWait(driver, 20)
        
        # Login with 2FA
        print("\n📍 Step 2: Login with 2FA...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed!")
            return False
        print("✅ Login successful!")
        
        # Navigate to listing page
        print("\n📍 Step 3: Navigate to Sell Inventory...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        
        print("📸 Taking form screenshot...")
        driver.save_screenshot("cellpex_form_before.png")
        
        # Fill form with enhanced methods
        print("\n📍 Step 4: Filling form with enhanced methods...")
        
        # Category (dropdown)
        try:
            category_select = wait.until(EC.presence_of_element_located((By.NAME, "selCateg")))
            category_dropdown = Select(category_select)
            try:
                category_dropdown.select_by_visible_text("Smartphones")
            except:
                category_dropdown.select_by_index(1)
            print("✅ Category selected")
        except Exception as e:
            print(f"⚠️  Category selection failed: {e}")
        
        # Brand (dropdown)
        try:
            brand_select = wait.until(EC.presence_of_element_located((By.NAME, "selBrand")))
            brand_dropdown = Select(brand_select)
            try:
                brand_dropdown.select_by_visible_text("Apple")
            except:
                brand_dropdown.select_by_index(1)
            print("✅ Brand selected")
        except Exception as e:
            print(f"⚠️  Brand selection failed: {e}")
        
        # Quantity
        enhanced_form_interaction(driver, "txtAvailable", str(test_data['quantity']))
        
        # Product name/model
        product_name = f"{test_data['brand']} {test_data['model']} {test_data['memory']}"
        enhanced_form_interaction(driver, "txtBrandModel", product_name)
        
        # Description (textarea) - This was failing before
        enhanced_form_interaction(driver, "areaComments", test_data['description'], "textarea")
        
        # Remarks (textarea) - This was failing before  
        remarks = f"Condition: {test_data['condition']} | Memory: {test_data['memory']} | Color: {test_data['color']}"
        enhanced_form_interaction(driver, "areaRemarks", remarks, "textarea")
        
        # Take screenshot after filling
        print("📸 Taking filled form screenshot...")
        driver.save_screenshot("cellpex_form_filled_fixed.png")
        
        # Enhanced submit
        print("\n📍 Step 5: Enhanced form submission...")
        
        submit_button = find_submit_button(driver)
        if submit_button:
            try:
                # Scroll to submit button
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(2)
                
                # Click submit
                submit_button.click()
                print("✅ Submit button clicked!")
                
                # Wait for response
                time.sleep(8)
                
                # Check result
                current_url = driver.current_url
                page_text = driver.page_source.lower()
                
                # Take post-submit screenshot
                driver.save_screenshot("cellpex_after_submit.png")
                print("📸 Post-submit screenshot saved")
                
                # Check for success/error
                success_indicators = ["success", "saved", "created", "posted", "added", "thank you"]
                error_indicators = ["error", "failed", "required", "invalid", "missing"]
                
                has_success = any(indicator in page_text for indicator in success_indicators)
                has_error = any(indicator in page_text for indicator in error_indicators)
                
                print(f"📍 Current URL: {current_url}")
                print(f"✅ Success indicators found: {has_success}")
                print(f"❌ Error indicators found: {has_error}")
                
                if has_success and not has_error:
                    print("🎉 LISTING CREATION SUCCESSFUL!")
                    result = "SUCCESS"
                elif has_error:
                    print("⚠️  Possible errors detected - manual verification needed")
                    result = "NEEDS_VERIFICATION" 
                else:
                    print("❓ Uncertain result - manual verification needed")
                    result = "UNCERTAIN"
                    
            except Exception as e:
                print(f"❌ Submit error: {e}")
                result = "SUBMIT_ERROR"
        else:
            print("❌ No submit button found")
            result = "NO_SUBMIT_BUTTON"
        
        # Final summary
        print(f"\n📊 FINAL RESULT: {result}")
        print("🔍 Browser kept open for manual verification...")
        print("📋 Check the screenshots and current state")
        print("Press Enter to close browser...")
        input()
        
        return result == "SUCCESS"
        
    except Exception as e:
        print(f"❌ Error in fixed listing flow: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("cellpex_error_fixed.png")
        
        print("\n🔍 Browser kept open for debugging...")
        input("Press Enter to close browser...")
        return False
        
    finally:
        try:
            driver.quit()
            print("✅ Browser closed")
        except:
            pass

if __name__ == "__main__":
    success = test_cellpex_fixed_listing()
    if success:
        print("\n🎉 CELLPEX LISTING FLOW COMPLETED SUCCESSFULLY!")
        print("✅ Ready to move to GSM Exchange!")
    else:
        print("\n🔧 Fixed flow needs further refinement")
        print("📋 Check screenshots for debugging")