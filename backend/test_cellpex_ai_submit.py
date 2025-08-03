#!/usr/bin/env python3
"""
AI-Powered Submit Button Finder
Uses GPT-4 Vision to find and click the correct submit button
"""

import os
import sys
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from intelligent_form_handler import IntelligentFormHandler
from selenium import webdriver
import time

def run_ai_submit_cellpex():
    """Use AI to find and click the submit button"""
    
    load_dotenv()
    
    # Check for required credentials
    if not all([os.getenv("CELLPEX_USERNAME"), os.getenv("CELLPEX_PASSWORD"), os.getenv("OPENAI_API_KEY")]):
        print("❌ Missing required credentials")
        return False
    
    print("🤖 AI-POWERED SUBMIT FINDER")
    print("="*50)
    
    # Test data
    listing_data = {
        "category": "Cell Phones",
        "brand": "Apple",
        "model": "iPhone 14 Pro Max",
        "memory": "512GB",
        "quantity": 3,
        "min_order": 1,
        "price": 1099.00,
        "condition": "New",
        "sim_lock": "Unlocked",
        "market_spec": "US Market",
        "carrier": "",
        "packing": "Original Box",
        "incoterm": "FOB",
        "available_date": datetime.now().strftime("%m/%d/%Y"),
        "item_weight": 0.5,
        "description": "Brand new iPhone 14 Pro Max 512GB. Factory sealed, never opened.",
        "remarks": "Premium flagship device"
    }
    
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
        ai_handler = IntelligentFormHandler(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(4)
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Fill form
        print("\n📍 Step 3: Filling form...")
        fill_results = field_mapper.map_and_fill_form(listing_data)
        success_count = sum(1 for v in fill_results.values() if v)
        print(f"✅ Filled {success_count}/{len(fill_results)} fields")
        
        # Take screenshot before AI analysis
        driver.save_screenshot("cellpex_ai_before_submit.png")
        
        # Step 4: Use AI to find submit button
        print("\n📍 Step 4: Using AI to find submit button...")
        
        # Get page structure
        page_structure = ai_handler.get_page_structure()
        screenshot = ai_handler.take_screenshot_base64()
        
        # Ask AI specifically about submit button
        submit_task = """I need to submit this wholesale inventory listing form on Cellpex. 
        The form is filled with all required data. 
        Please analyze the page and tell me:
        1. Where is the submit/save button located?
        2. What text does it have?
        3. What's the best way to click it?
        
        IMPORTANT: This is the LISTING form, not the search form at the top of the page.
        
        Provide instructions to click the correct submit button."""
        
        ai_response = ai_handler.ask_ai_for_guidance(
            submit_task, 
            page_structure, 
            screenshot,
            {"task": "submit_form"}
        )
        
        print(f"\n🤖 AI Response: {ai_response}")
        
        # Step 5: Execute AI instructions
        print("\n📍 Step 5: Executing AI submit instructions...")
        
        if "actions" in ai_response:
            # Execute AI actions
            success = ai_handler.execute_ai_instructions(ai_response)
            
            if success:
                print("✅ AI successfully clicked submit!")
                
                # Wait for submission
                time.sleep(5)
                
                # Take final screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_screenshot = f"cellpex_ai_submit_final_{timestamp}.png"
                driver.save_screenshot(final_screenshot)
                print(f"📸 Final screenshot: {final_screenshot}")
                
                # Check result
                final_url = driver.current_url
                print(f"\n📍 Final URL: {final_url}")
                
                if "success" in final_url or "posted" in final_url:
                    print("🎉 LISTING POSTED SUCCESSFULLY!")
                    return True
                else:
                    # Ask AI to analyze result
                    print("\n🤖 AI analyzing result...")
                    result_analysis = ai_handler.handle_unexpected_situation(
                        "Did the form submit successfully? Are there any errors?"
                    )
                    print(f"📊 Analysis: {result_analysis}")
            else:
                print("❌ AI couldn't execute submit")
        else:
            # Fallback: Try manual submit
            print("\n📍 Fallback: Trying manual submit...")
            
            # Use the specific submit button finding logic
            submitted = driver.execute_script("""
                // Find all forms
                var forms = document.querySelectorAll('form');
                
                for (var i = 0; i < forms.length; i++) {
                    var form = forms[i];
                    
                    // Check if this is the listing form
                    if (form.querySelector('input[name="txtBrandModel"]')) {
                        console.log('Found listing form');
                        
                        // Find all possible submit elements
                        var submitElements = form.querySelectorAll(
                            'input[type="submit"], button[type="submit"], ' +
                            'button:not([type]), input[type="button"][value*="Save"], ' +
                            'input[type="button"][value*="Submit"], button[class*="submit"]'
                        );
                        
                        console.log('Found ' + submitElements.length + ' potential submit buttons');
                        
                        for (var j = 0; j < submitElements.length; j++) {
                            var btn = submitElements[j];
                            if (btn.offsetParent !== null) {
                                console.log('Clicking: ' + btn.outerHTML);
                                btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(function() {
                                    btn.click();
                                }, 500);
                                return true;
                            }
                        }
                    }
                }
                
                return false;
            """)
            
            if submitted:
                print("✅ Manual submit successful!")
            else:
                print("❌ Manual submit failed")
        
        # Keep browser open briefly
        print("\n⏳ Browser closing in 10 seconds...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            error_screenshot = f"cellpex_ai_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🤖 CELLPEX AI SUBMIT FINDER")
    print("="*50)
    
    success = run_ai_submit_cellpex()
    
    if success:
        print("\n✅ AI submit test completed!")
    else:
        print("\n❌ AI submit test failed!")
    
    sys.exit(0 if success else 1)