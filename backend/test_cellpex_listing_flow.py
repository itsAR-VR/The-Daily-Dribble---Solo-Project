#!/usr/bin/env python3
"""
Test Cellpex complete flow: Login → Navigate to listing → Submit test listing
"""

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def test_cellpex_listing_flow():
    """Test complete Cellpex listing flow"""
    
    # Load credentials
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"🚀 Testing Cellpex listing flow...")
    print(f"   Username: {username}")
    
    # Create driver
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920x1080")
    # Keep visible for debugging
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Step 1: Login
        print("\n📍 Step 1: Login to Cellpex...")
        driver.get("https://www.cellpex.com/login")
        
        # Fill login form
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "txtUser")))
        user_field.clear()
        user_field.send_keys(username)
        
        pass_field = wait.until(EC.presence_of_element_located((By.NAME, "txtPass")))
        pass_field.clear()
        pass_field.send_keys(password)
        
        submit = wait.until(EC.element_to_be_clickable((By.NAME, "btnLogin")))
        submit.click()
        
        print("✅ Login form submitted")
        
        # Wait for redirect
        time.sleep(5)
        
        # Check if we're logged in
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        # Check for 2FA
        page_source = driver.page_source.lower()
        if any(term in page_source for term in ['verification', '2fa', 'authenticate', 'code']):
            print("⚠️  2FA detected - this needs to be handled")
            # Take screenshot for analysis
            driver.save_screenshot("cellpex_2fa_required.png")
            return False
        
        # Check if login successful
        if "login" in current_url:
            print("❌ Still on login page - login may have failed")
            # Check for error messages
            try:
                error_elem = driver.find_element(By.CSS_SELECTOR, ".error, .alert-danger, .message")
                print(f"❌ Error message: {error_elem.text}")
            except:
                print("❌ No specific error message found")
            return False
        
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigate to listing page...")
        
        # Try different methods to get to listing page
        listing_urls = [
            "https://www.cellpex.com/seller/products/create",
            "https://www.cellpex.com/post-listing",
            "https://www.cellpex.com/sell",
            "https://www.cellpex.com/add-product"
        ]
        
        listing_page_found = False
        for url in listing_urls:
            try:
                driver.get(url)
                time.sleep(3)
                
                # Check if we're on a listing page
                if any(term in driver.page_source.lower() for term in ['product', 'listing', 'sell', 'add']):
                    print(f"✅ Found listing page at: {url}")
                    listing_page_found = True
                    break
            except:
                continue
        
        if not listing_page_found:
            print("❌ Could not find listing page")
            # Try to find a link
            try:
                sell_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Sell")
                sell_link.click()
                print("✅ Clicked 'Sell' link")
            except:
                print("❌ No 'Sell' link found")
                
        # Step 3: Analyze listing form
        print("\n📍 Step 3: Analyzing listing form...")
        time.sleep(3)
        
        # Find all input fields
        input_fields = driver.find_elements(By.TAG_NAME, "input")
        print(f"📊 Found {len(input_fields)} input fields")
        
        # Find all select dropdowns
        select_fields = driver.find_elements(By.TAG_NAME, "select")
        print(f"📊 Found {len(select_fields)} select fields")
        
        # Find all textareas
        textarea_fields = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"📊 Found {len(textarea_fields)} textarea fields")
        
        # Document form structure
        print("\n📋 Form Fields Found:")
        
        for i, field in enumerate(input_fields[:10]):  # First 10 inputs
            field_name = field.get_attribute("name") or "no-name"
            field_id = field.get_attribute("id") or "no-id"
            field_type = field.get_attribute("type") or "text"
            field_placeholder = field.get_attribute("placeholder") or ""
            
            if field_type not in ['hidden', 'submit']:
                print(f"  Input {i+1}: name='{field_name}', type='{field_type}', placeholder='{field_placeholder}'")
        
        for i, field in enumerate(select_fields[:5]):  # First 5 selects
            field_name = field.get_attribute("name") or "no-name"
            field_id = field.get_attribute("id") or "no-id"
            print(f"  Select {i+1}: name='{field_name}', id='{field_id}'")
        
        # Step 4: Try to fill a test listing
        print("\n📍 Step 4: Attempting to fill test listing...")
        
        # Common field names to try
        field_mappings = {
            'product_name': ['name', 'product_name', 'title', 'product', 'item_name'],
            'quantity': ['qty', 'quantity', 'stock', 'amount'],
            'price': ['price', 'cost', 'amount', 'value'],
            'description': ['description', 'desc', 'details', 'info']
        }
        
        test_data = {
            'product_name': 'Test iPhone 15 Pro Max',
            'quantity': '10',
            'price': '999',
            'description': 'Test listing - please ignore'
        }
        
        filled_fields = []
        
        for field_type, field_names in field_mappings.items():
            for field_name in field_names:
                try:
                    # Try by name
                    field = driver.find_element(By.NAME, field_name)
                    field.clear()
                    field.send_keys(test_data.get(field_type, ''))
                    filled_fields.append(f"{field_type} (name={field_name})")
                    print(f"✅ Filled {field_type} field")
                    break
                except:
                    try:
                        # Try by id
                        field = driver.find_element(By.ID, field_name)
                        field.clear()
                        field.send_keys(test_data.get(field_type, ''))
                        filled_fields.append(f"{field_type} (id={field_name})")
                        print(f"✅ Filled {field_type} field")
                        break
                    except:
                        continue
        
        print(f"\n📊 Successfully filled {len(filled_fields)} fields:")
        for field in filled_fields:
            print(f"   - {field}")
        
        # Take screenshot of filled form
        driver.save_screenshot("cellpex_listing_form_filled.png")
        print("📸 Screenshot saved: cellpex_listing_form_filled.png")
        
        # Don't actually submit - just for testing
        print("\n⚠️  Form filled but NOT submitted (test mode)")
        
        # Find submit button for reference
        try:
            submit_button = driver.find_element(By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], button:contains('Submit'), button:contains('Post')")
            print(f"✅ Found submit button: {submit_button.text or submit_button.get_attribute('value')}")
        except:
            print("❌ Could not find submit button")
        
        print("\n✅ Cellpex listing flow test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        # Take error screenshot
        driver.save_screenshot("cellpex_error.png")
        return False
    finally:
        print("\n🔍 Browser left open for inspection...")
        input("Press Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    test_cellpex_listing_flow()