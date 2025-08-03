#!/usr/bin/env python3
"""
Production-Ready Cellpex Listing Bot
Combines field mapping, AI assistance, and proper error handling
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from intelligent_form_handler import IntelligentFormHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json

def run_production_cellpex(user_listing_data: Dict = None):
    """Production-ready Cellpex listing with all features"""
    
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([username, password]):
        print("❌ Missing Cellpex credentials")
        return False
    
    print("🚀 PRODUCTION CELLPEX LISTING BOT")
    print("="*50)
    
    # Use provided data or test data
    if not user_listing_data:
        user_listing_data = {
            "category": "Cell Phones",
            "brand": "Apple", 
            "model": "iPhone 14 Pro",
            "memory": "256GB",
            "quantity": 5,
            "min_order": 1,
            "price": 899.00,
            "condition": "New",
            "sim_lock": "Unlocked",
            "market_spec": "US Market",
            "carrier": "",
            "packing": "Original Box",
            "incoterm": "FOB",
            "available_date": datetime.now().strftime("%m/%d/%Y"),
            "item_weight": 0.5,
            "description": "Brand new iPhone 14 Pro, factory sealed. Fast shipping.",
            "remarks": "Premium device, handle with care"
        }
    
    print(f"📦 Listing: {user_listing_data.get('brand')} {user_listing_data.get('model')}")
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        
        # Initialize components
        cellpex_poster = EnhancedCellpexPoster(driver)
        field_mapper = CellpexFieldMapper(driver)
        ai_handler = IntelligentFormHandler(driver, openai_key) if openai_key else None
        
        # Step 1: Login
        print("\n📍 Step 1: Login with 2FA...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed")
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(4)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Take screenshot of empty form
        driver.save_screenshot("cellpex_production_empty.png")
        
        # Step 3: Fill form using field mapper
        print("\n📍 Step 3: Filling form with field mapper...")
        fill_results = field_mapper.map_and_fill_form(user_listing_data)
        
        # Print results
        success_count = sum(1 for v in fill_results.values() if v)
        print(f"\n📊 Field filling results: {success_count}/{len(fill_results)} successful")
        
        for field, success in fill_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {field}")
        
        # Take screenshot after filling
        driver.save_screenshot("cellpex_production_filled.png")
        
        # Step 4: Check for missing fields
        print("\n📍 Step 4: Checking for missing required fields...")
        missing = field_mapper.get_missing_fields()
        
        if missing:
            print(f"⚠️ Missing required fields: {missing}")
            
            # If AI is available, ask for help
            if ai_handler:
                print("\n🤖 Using AI to complete missing fields...")
                task = f"Fill the missing required fields: {missing}"
                ai_success, ai_msg = ai_handler.handle_form_intelligently(
                    task, user_listing_data
                )
                if ai_success:
                    print(f"✅ AI filled missing fields")
                else:
                    print(f"❌ AI couldn't fill all fields: {ai_msg}")
        else:
            print("✅ All required fields filled!")
        
        # Step 5: Submit form
        print("\n📍 Step 5: Submitting form...")
        
        # Find and click the correct submit button
        submitted = driver.execute_script("""
            // Find the listing form
            var forms = document.querySelectorAll('form');
            for (var i = 0; i < forms.length; i++) {
                var form = forms[i];
                
                // Check if this is the listing form
                if (form.querySelector('input[name="txtBrandModel"]')) {
                    // Find submit button
                    var submitBtn = form.querySelector(
                        'input[type="submit"], button[type="submit"]'
                    );
                    
                    if (submitBtn && submitBtn.offsetParent !== null) {
                        // Highlight button
                        submitBtn.style.border = '3px solid green';
                        
                        // Scroll to button
                        submitBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        
                        // Click after delay
                        setTimeout(function() {
                            submitBtn.click();
                            console.log('Form submitted');
                        }, 1000);
                        
                        return true;
                    }
                }
            }
            return false;
        """)
        
        if submitted:
            print("✅ Form submitted!")
        else:
            print("❌ Could not find submit button")
        
        # Wait for result
        print("\n⏳ Waiting for submission result...")
        time.sleep(8)
        
        # Take final screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"cellpex_production_final_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        print(f"📸 Final screenshot: {final_screenshot}")
        
        # Step 6: Analyze result
        print("\n📍 Step 6: Analyzing result...")
        
        final_url = driver.current_url
        print(f"📍 Final URL: {final_url}")
        
        # Check for errors
        errors = field_mapper.analyze_form_errors()
        
        if errors:
            print("\n⚠️ Form validation errors found:")
            for error in errors:
                print(f"  - {error}")
                
            # Use AI to understand errors if available
            if ai_handler:
                print("\n🤖 AI analyzing errors...")
                error_help = ai_handler.handle_unexpected_situation(
                    f"Form has these errors: {errors}"
                )
                print(f"💡 AI suggestion: {error_help}")
        else:
            # Check page content for success
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            if "success" in page_text or "posted" in page_text:
                print("🎉 LISTING POSTED SUCCESSFULLY!")
                return True
            elif "wholesale-inventory" in final_url and "list" in final_url:
                print("📍 Still on form page - submission may have failed")
            else:
                print("❓ Unknown result - check screenshot")
        
        # Keep browser open briefly for review
        print("\n⏳ Browser closing in 5 seconds...")
        time.sleep(5)
        
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            error_screenshot = f"cellpex_production_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            
            # Use AI to diagnose if available
            if 'ai_handler' in locals() and ai_handler:
                try:
                    diagnosis = ai_handler.handle_unexpected_situation(str(e))
                    print(f"\n🤖 AI diagnosis: {diagnosis}")
                except:
                    pass
                
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🚀 CELLPEX PRODUCTION LISTING BOT")
    print("="*50)
    
    # Example: Read from command line args or use test data
    if len(sys.argv) > 1:
        try:
            user_data = json.loads(sys.argv[1])
            print("📋 Using provided listing data")
        except:
            print("⚠️ Invalid JSON provided, using test data")
            user_data = None
    else:
        print("📋 Using test data (no data provided)")
        user_data = None
    
    success = run_production_cellpex(user_data)
    
    if success:
        print("\n✅ Production listing completed!")
    else:
        print("\n❌ Production listing failed!")
    
    sys.exit(0 if success else 1)