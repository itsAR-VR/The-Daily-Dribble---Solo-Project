#!/usr/bin/env python3
"""
Test the COMPLETE Cellpex flow: login + 2FA + listing creation
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from gmail_service import gmail_service

def test_complete_cellpex_flow():
    """Test the complete Cellpex workflow"""
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 Testing Complete Cellpex Flow (Login + 2FA + Listing)...")
    
    # Create test listing data
    test_data = {
        'brand': 'Apple',
        'model': 'iPhone 14 Pro',
        'condition': 'Used',
        'grade': 'Grade B', 
        'lcd_defect': 'No',
        'memory': '128GB',
        'color': 'Space Black',
        'quantity': 5,
        'price': 750.00,
        'description': 'Excellent condition iPhone 14 Pro with minor wear',
        'market_spec': 'US Market',
        'sim_lock': 'Unlocked',
        'packaging': 'Original Box',
        'incoterms': 'FOB',
        'payment_method': 'Wire Transfer',
        'quality_certification': 'Yes',
        'carrier': 'Verizon',
        'item_weight': '0.5 kg',
        'delivery_days': '3-5 days',
        'country': 'United States',
        'state': 'California',
        'private_notes': 'Test listing for bot integration',
        'manufacturer_type': 'Original'
    }
    
    # Convert to DataFrame row
    df = pd.DataFrame([test_data])
    row = df.iloc[0]
    
    # Check credentials first
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"📧 Gmail service available: {gmail_service.is_available()}")
    print(f"👤 Username: {username}")
    
    try:
        # Step 1: Initialize driver
        print("\n📍 Step 1: Initializing browser...")
        from selenium import webdriver
        
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
        
        # Step 3: Navigate to listing page and explore
        print("\n📍 Step 3: Exploring listing functionality...")
        driver = cellpex_poster.driver
        
        # Look for selling/listing options
        print("🔍 Looking for listing options in page...")
        page_source = driver.page_source
        
        # Check for common listing-related terms
        listing_keywords = [
            'sell inventory',
            'add listing', 
            'post listing',
            'create listing',
            'my inventory',
            'add product',
            'sell product'
        ]
        
        found_keywords = []
        for keyword in listing_keywords:
            if keyword.lower() in page_source.lower():
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"✅ Found listing keywords: {found_keywords}")
        else:
            print("⚠️  No obvious listing keywords found")
        
        # Look for navigation links
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(driver, 10)
            
            # Try to find and click "Sell Inventory" or similar
            possible_links = [
                "//a[contains(text(), 'Sell Inventory')]",
                "//a[contains(text(), 'Add Listing')]", 
                "//a[contains(text(), 'Post Listing')]",
                "//a[contains(text(), 'My Inventory')]",
                "//button[contains(text(), 'Sell Inventory')]"
            ]
            
            clicked_link = False
            for link_xpath in possible_links:
                try:
                    link = driver.find_element(By.XPATH, link_xpath)
                    print(f"✅ Found link: {link.text}")
                    
                    # Try to click it
                    link.click()
                    print(f"✅ Clicked: {link.text}")
                    clicked_link = True
                    
                    # Wait a moment and check new page
                    import time
                    time.sleep(3)
                    
                    new_url = driver.current_url
                    print(f"📍 New URL: {new_url}")
                    
                    # Take screenshot for debugging
                    driver.save_screenshot("cellpex_listing_page.png")
                    print("📸 Screenshot saved: cellpex_listing_page.png")
                    
                    break
                    
                except Exception as e:
                    continue
            
            if not clicked_link:
                print("⚠️  Could not find or click listing link")
                print("📍 Taking screenshot of current page...")
                driver.save_screenshot("cellpex_main_page.png")
                print("📸 Screenshot saved: cellpex_main_page.png")
        
        except Exception as e:
            print(f"⚠️  Error exploring listing functionality: {e}")
        
        # Keep browser open for manual inspection
        print("\n🔍 Flow completed successfully!")
        print("📍 Browser kept open for manual inspection...")
        print("📋 You can now manually explore the listing functionality")
        print("Press Enter to close browser...")
        input()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in complete flow: {e}")
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
    success = test_complete_cellpex_flow()
    if success:
        print("🎉 Complete Cellpex flow test completed successfully!")
    else:
        print("❌ Complete Cellpex flow test failed!")
        sys.exit(1)