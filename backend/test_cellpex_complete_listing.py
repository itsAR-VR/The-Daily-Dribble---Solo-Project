#!/usr/bin/env python3
"""
Test Complete Cellpex Flow: Login + 2FA + Create Actual Listing
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from gmail_service import gmail_service
from selenium import webdriver

def test_complete_cellpex_listing():
    """Test the complete Cellpex workflow: login + 2FA + actual listing creation"""
    
    # Load environment variables
    load_dotenv()
    
    # Check credentials first
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing Cellpex credentials!")
        return False
    
    print(f"🚀 Testing Complete Cellpex Listing Flow...")
    print(f"   Username: {username}")
    print(f"📧 Gmail service available: {gmail_service.is_available()}")
    
    # Create realistic test listing data
    test_data = {
        'brand': 'Apple',
        'model': 'iPhone 14 Pro',
        'condition': 'Used - Excellent',
        'condition_grade': 'Grade A', 
        'lcd_defects': 'No',
        'memory': '256GB',
        'color': 'Deep Purple',
        'quantity': 3,
        'price': 850.00,
        'description': 'Excellent condition iPhone 14 Pro with minimal wear. Fully tested and functional. Original box included.',
        'market_spec': 'US Market',
        'sim_lock_status': 'Unlocked',
        'packaging': 'Original Box',
        'incoterm': 'FOB',
        'payment_method': 'Wire Transfer',
        'quality_certification': 'Yes',
        'carrier': 'Unlocked',
        'item_weight': '0.6 kg',
        'delivery_days': '2-3 business days',
        'country': 'United States',
        'state': 'California',
        'private_notes': 'Test listing created by automation bot',
        'manufacturer_type': 'Original'
    }
    
    # Convert to DataFrame row
    df = pd.DataFrame([test_data])
    row = df.iloc[0]
    
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
        
        print("✅ Login with 2FA successful!")
        
        # Step 3: Create actual listing
        print("\n📍 Step 3: Creating listing...")
        print(f"📦 Product: {test_data['brand']} {test_data['model']} {test_data['memory']}")
        print(f"💰 Price: ${test_data['price']}")
        print(f"📊 Quantity: {test_data['quantity']}")
        print(f"🏷️ Condition: {test_data['condition']}")
        
        # Use the enhanced post_listing method
        result = cellpex_poster.post_listing(row)
        
        print(f"\n📋 Listing Result: {result}")
        
        if "Success" in result:
            print("🎉 COMPLETE SUCCESS! Cellpex listing created successfully!")
            print("\n📊 Final Summary:")
            print("✅ Login: SUCCESS")
            print("✅ 2FA: SUCCESS") 
            print("✅ Listing Creation: SUCCESS")
            
            # Keep browser open for verification
            print("\n🔍 Browser kept open for manual verification...")
            print("📋 You can manually verify the listing was created")
            print("Press Enter to close browser...")
            input()
            
            return True
        else:
            print(f"❌ Listing creation failed: {result}")
            print("\n📊 Partial Success Summary:")
            print("✅ Login: SUCCESS")
            print("✅ 2FA: SUCCESS")
            print("❌ Listing Creation: FAILED")
            
            # Keep browser open for debugging
            print("\n🔍 Browser kept open for debugging...")
            print("📋 You can manually inspect what went wrong")
            print("Press Enter to close browser...")
            input()
            
            return False
        
    except Exception as e:
        print(f"❌ Error in complete listing flow: {e}")
        import traceback
        traceback.print_exc()
        
        # Keep browser open for debugging
        try:
            print("\n🔍 Browser kept open for debugging...")
            print("📋 You can manually inspect the error state")
            print("Press Enter to close browser...")
            input()
        except:
            pass
        
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
    success = test_complete_cellpex_listing()
    if success:
        print("\n🎉 COMPLETE CELLPEX FLOW TEST PASSED!")
        print("✅ Ready for production multi-platform listing!")
    else:
        print("\n❌ Complete Cellpex flow test failed!")
        print("🔧 Check the logs and screenshots for debugging")
        sys.exit(1)