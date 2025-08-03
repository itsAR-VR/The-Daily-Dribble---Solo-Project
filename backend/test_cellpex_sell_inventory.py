#!/usr/bin/env python3
"""
Test Cellpex SELL INVENTORY Flow
Focus on navigating to the listing creation page, not just viewing inventory
"""

import os
import time
import pandas as pd
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from gmail_service import gmail_service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def test_cellpex_sell_inventory_flow():
    """Test complete Cellpex flow: login + 2FA + navigate to SELL INVENTORY"""
    
    # Load environment variables
    load_dotenv()
    
    # Check credentials first
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"🚀 Testing Cellpex SELL INVENTORY Flow...")
    print(f"   Username: {username}")
    print(f"📧 Gmail service available: {gmail_service.is_available()}")
    
    try:
        # Step 1: Initialize driver
        print("\n📍 Step 1: Initializing browser...")
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        # Keep visible for debugging
        driver = webdriver.Chrome(options=options)
        print("✅ Browser initialized")
        
        # Initialize poster with driver
        cellpex_poster = EnhancedCellpexPoster(driver)
        print("✅ Cellpex poster initialized")
        
        # Step 2: Login with 2FA
        print("\n📍 Step 2: Login with 2FA...")
        login_success = cellpex_poster.login_with_2fa()
        
        if not login_success:
            print("❌ Login failed!")
            return False
        
        print("✅ Login successful!")
        
        # Step 3: Navigate to SELL INVENTORY specifically
        print("\n📍 Step 3: Navigating to SELL INVENTORY...")
        wait = WebDriverWait(driver, 20)
        
        # Take screenshot of current page for reference
        driver.save_screenshot("cellpex_dashboard.png")
        print("📸 Dashboard screenshot saved: cellpex_dashboard.png")
        
        # Look specifically for "Sell Inventory" link/button
        sell_inventory_selectors = [
            "//a[contains(text(), 'Sell Inventory')]",
            "//button[contains(text(), 'Sell Inventory')]",
            "//a[contains(@href, 'sell') and contains(text(), 'Inventory')]",
            "//a[contains(@href, 'add') and contains(text(), 'Inventory')]",
            "//a[contains(@href, 'post') and contains(text(), 'Inventory')]",
            "//div[contains(@class, 'sell')]//a[contains(text(), 'Inventory')]",
            "//nav//a[contains(text(), 'Sell Inventory')]",
            "//li//a[contains(text(), 'Sell Inventory')]"
        ]
        
        sell_link_found = False
        for selector in sell_inventory_selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                sell_link = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                
                # Get link details before clicking
                link_text = sell_link.text
                link_href = sell_link.get_attribute('href')
                print(f"✅ Found 'Sell Inventory' link:")
                print(f"   Text: '{link_text}'")
                print(f"   URL: {link_href}")
                
                # Click the link
                sell_link.click()
                sell_link_found = True
                print(f"✅ Clicked 'Sell Inventory' link")
                
                # Wait for page to load
                time.sleep(3)
                
                # Check new URL
                new_url = driver.current_url
                print(f"📍 New URL after clicking: {new_url}")
                
                # Take screenshot of sell inventory page
                driver.save_screenshot("cellpex_sell_inventory_page.png")
                print("📸 Sell Inventory page screenshot: cellpex_sell_inventory_page.png")
                
                break
                
            except Exception as e:
                print(f"⚠️  Selector failed: {selector}")
                continue
        
        if not sell_link_found:
            print("❌ Could not find 'Sell Inventory' link")
            
            # Debug: Print available links
            print("\n🔍 Available links on page:")
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for i, link in enumerate(links[:20]):  # Show first 20 links
                    link_text = link.text.strip()
                    link_href = link.get_attribute('href')
                    if link_text:  # Only show links with text
                        print(f"  {i+1}. '{link_text}' -> {link_href}")
            except Exception as e:
                print(f"   Error getting links: {e}")
            
            return False
        
        # Step 4: Analyze the sell inventory page
        print("\n📍 Step 4: Analyzing sell inventory page...")
        
        page_source = driver.page_source.lower()
        
        # Look for form elements that suggest this is a listing creation page
        listing_indicators = [
            'add listing',
            'create listing', 
            'post listing',
            'new listing',
            'product name',
            'product title',
            'item name',
            'description',
            'price',
            'quantity',
            'condition',
            'brand',
            'model'
        ]
        
        found_indicators = []
        for indicator in listing_indicators:
            if indicator in page_source:
                found_indicators.append(indicator)
        
        if found_indicators:
            print(f"✅ Found listing creation indicators: {found_indicators}")
        else:
            print("⚠️  No obvious listing creation indicators found")
        
        # Look for form fields
        print("\n🔍 Looking for form fields...")
        try:
            # Common form field types for listing creation
            form_fields = {
                'text_inputs': driver.find_elements(By.CSS_SELECTOR, "input[type='text']"),
                'textareas': driver.find_elements(By.TAG_NAME, "textarea"),
                'selects': driver.find_elements(By.TAG_NAME, "select"),
                'file_inputs': driver.find_elements(By.CSS_SELECTOR, "input[type='file']"),
                'number_inputs': driver.find_elements(By.CSS_SELECTOR, "input[type='number']")
            }
            
            for field_type, elements in form_fields.items():
                if elements:
                    print(f"✅ Found {len(elements)} {field_type}")
                    
                    # Show details for first few elements
                    for i, element in enumerate(elements[:3]):
                        name = element.get_attribute('name')
                        placeholder = element.get_attribute('placeholder')
                        id_attr = element.get_attribute('id')
                        print(f"   {i+1}. name='{name}', placeholder='{placeholder}', id='{id_attr}'")
                        
        except Exception as e:
            print(f"⚠️  Error analyzing form fields: {e}")
        
        # Step 5: Look for submit/save buttons
        print("\n🔍 Looking for submit buttons...")
        try:
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Save')",
                "button:contains('Add')",
                "button:contains('Create')",
                "button:contains('Post')",
                "button:contains('Submit')"
            ]
            
            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        # Convert to xpath
                        xpath_selector = selector.replace("button:contains('", "//button[contains(text(), '").replace("')", "')]")
                        buttons = driver.find_elements(By.XPATH, xpath_selector)
                    else:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if buttons:
                        print(f"✅ Found {len(buttons)} buttons for selector: {selector}")
                        for i, btn in enumerate(buttons[:2]):
                            btn_text = btn.text.strip()
                            print(f"   {i+1}. '{btn_text}'")
                            
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Error analyzing submit buttons: {e}")
        
        print(f"\n🎉 Successfully navigated to Cellpex Sell Inventory page!")
        print(f"📍 Current URL: {driver.current_url}")
        
        # Keep browser open for manual inspection
        print("\n🔍 Browser kept open for manual inspection...")
        print("📋 You can now manually explore the listing creation form")
        print("Press Enter to close browser...")
        input()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in sell inventory flow: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        try:
            if 'driver' in locals():
                driver.quit()
                print("✅ Browser closed")
        except:
            pass


if __name__ == "__main__":
    success = test_cellpex_sell_inventory_flow()
    if success:
        print("🎉 Cellpex Sell Inventory flow test completed successfully!")
    else:
        print("❌ Cellpex Sell Inventory flow test failed!")
        import sys
        sys.exit(1)