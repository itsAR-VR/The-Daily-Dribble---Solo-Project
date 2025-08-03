#!/usr/bin/env python3
"""
COMPLETE Cellpex Form - Fill ALL required fields
"""

import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys

def run_complete_cellpex_listing():
    """Complete listing with ALL required fields"""
    
    load_dotenv()
    username = os.getenv("CELLPEX_USERNAME")
    password = os.getenv("CELLPEX_PASSWORD")
    
    if not username or not password:
        print("❌ Missing credentials")
        return False
    
    print("📋 COMPLETE MODE: Filling ALL required fields...")
    
    # Complete test data with ALL fields
    test_data = {
        'category': 'Smartphones',
        'brand': 'Apple',
        'model': 'iPhone 14 Pro',
        'memory': '256GB',
        'quantity': 5,
        'min_order': 1,
        'price': 899.00,
        'description': 'Brand new condition. Factory unlocked.',
        'condition': 'New',
        'sim_lock': 'Unlocked',
        'market_spec': 'US Market',
        'packing': 'Original Box',
        'incoterm': 'FOB',
        'available_from': datetime.now().strftime('%m/%d/%Y'),
        'item_weight': '0.5',
        'carrier': ''  # Empty for unlocked
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
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📝 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(4)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Fill ALL form fields
        print("\n📋 Step 3: Filling ALL required fields...")
        
        # Use JavaScript to fill all fields at once
        fill_result = driver.execute_script("""
            var filled = [];
            
            // Category dropdown
            try {
                var catSelect = document.querySelector('select[name="selCateg"]');
                if (catSelect) {
                    catSelect.value = catSelect.querySelector('option[value*="phone"]')?.value || catSelect.options[1].value;
                    catSelect.dispatchEvent(new Event('change'));
                    filled.push('Category');
                }
            } catch(e) {}
            
            // Brand dropdown
            try {
                var brandSelect = document.querySelector('select[name="selBrand"]');
                if (brandSelect) {
                    // Find Apple option
                    for (var i = 0; i < brandSelect.options.length; i++) {
                        if (brandSelect.options[i].text.includes('Apple')) {
                            brandSelect.value = brandSelect.options[i].value;
                            break;
                        }
                    }
                    brandSelect.dispatchEvent(new Event('change'));
                    filled.push('Brand');
                }
            } catch(e) {}
            
            // Available from date
            try {
                var dateField = document.querySelector('input[name="txtAvailable"]');
                if (dateField) {
                    dateField.value = arguments[0];
                    dateField.dispatchEvent(new Event('change'));
                    filled.push('Available date');
                }
            } catch(e) {}
            
            // Product name
            try {
                var prodField = document.querySelector('input[name="txtBrandModel"]');
                if (prodField) {
                    prodField.value = arguments[1];
                    prodField.dispatchEvent(new Event('change'));
                    filled.push('Product');
                }
            } catch(e) {}
            
            // Condition dropdown
            try {
                var condSelect = document.querySelector('select[name="selCondition"]');
                if (condSelect) {
                    condSelect.value = condSelect.querySelector('option[value*="New"]')?.value || condSelect.options[1].value;
                    condSelect.dispatchEvent(new Event('change'));
                    filled.push('Condition');
                }
            } catch(e) {}
            
            // Market Spec dropdown
            try {
                var marketSelect = document.querySelector('select[name="selMarketSpec"]');
                if (marketSelect) {
                    marketSelect.value = marketSelect.querySelector('option[value*="US"]')?.value || marketSelect.options[1].value;
                    marketSelect.dispatchEvent(new Event('change'));
                    filled.push('Market Spec');
                }
            } catch(e) {}
            
            // SIM Lock dropdown
            try {
                var simSelect = document.querySelector('select[name="selSIMlock"]');
                if (simSelect) {
                    simSelect.value = simSelect.querySelector('option[value*="Unlock"]')?.value || simSelect.options[1].value;
                    simSelect.dispatchEvent(new Event('change'));
                    filled.push('SIM Lock');
                }
            } catch(e) {}
            
            // Carrier field (if exists)
            try {
                var carrierField = document.querySelector('input[name="txtCarrier"]');
                if (carrierField) {
                    carrierField.value = '';  // Empty for unlocked
                    carrierField.dispatchEvent(new Event('change'));
                    filled.push('Carrier');
                }
            } catch(e) {}
            
            // Price field
            try {
                var priceField = document.querySelector('input[name="txtPrice"]');
                if (priceField) {
                    priceField.value = arguments[2];
                    priceField.dispatchEvent(new Event('change'));
                    filled.push('Price');
                }
            } catch(e) {}
            
            // Quantity field
            try {
                var qtyField = document.querySelector('input[name="txtQuantity"]');
                if (qtyField) {
                    qtyField.value = arguments[3];
                    qtyField.dispatchEvent(new Event('change'));
                    filled.push('Quantity');
                }
            } catch(e) {}
            
            // Min Order field
            try {
                var minField = document.querySelector('input[name="txtMinOrder"]');
                if (minField) {
                    minField.value = '1';
                    minField.dispatchEvent(new Event('change'));
                    filled.push('Min Order');
                }
            } catch(e) {}
            
            // Item weight
            try {
                var weightField = document.querySelector('input[name="txtWeight"]');
                if (weightField) {
                    weightField.value = '0.5';
                    weightField.dispatchEvent(new Event('change'));
                    filled.push('Weight');
                }
            } catch(e) {}
            
            // Packing dropdown
            try {
                var packSelect = document.querySelector('select[name="selPacking"]');
                if (packSelect) {
                    packSelect.value = packSelect.querySelector('option[value*="Original"]')?.value || packSelect.options[1].value;
                    packSelect.dispatchEvent(new Event('change'));
                    filled.push('Packing');
                }
            } catch(e) {}
            
            // Incoterm dropdown
            try {
                var incoSelect = document.querySelector('select[name="selIncoterm"]');
                if (incoSelect) {
                    incoSelect.value = incoSelect.querySelector('option[value*="FOB"]')?.value || incoSelect.options[1].value;
                    incoSelect.dispatchEvent(new Event('change'));
                    filled.push('Incoterm');
                }
            } catch(e) {}
            
            // Description textarea
            try {
                var descField = document.querySelector('textarea[name="areaComments"]');
                if (descField) {
                    descField.value = arguments[4];
                    descField.dispatchEvent(new Event('change'));
                    filled.push('Description');
                }
            } catch(e) {}
            
            // Remarks textarea
            try {
                var remField = document.querySelector('textarea[name="areaRemarks"]');
                if (remField) {
                    remField.value = 'Memory: ' + arguments[5] + ' | Excellent condition | Fast shipping';
                    remField.dispatchEvent(new Event('change'));
                    filled.push('Remarks');
                }
            } catch(e) {}
            
            return filled;
        """, 
            test_data['available_from'],
            f"{test_data['brand']} {test_data['model']}",
            str(test_data['price']),
            str(test_data['quantity']),
            test_data['description'],
            test_data['memory']
        )
        
        print(f"✅ Filled fields: {', '.join(fill_result)}")
        print(f"📊 Total: {len(fill_result)} fields filled")
        
        # Take screenshot
        driver.save_screenshot("cellpex_complete_filled.png")
        print("📸 Complete form screenshot saved")
        
        # Step 4: Submit the form
        print("\n🚀 Step 4: Submitting complete form...")
        
        # Find and click submit button
        submit_clicked = driver.execute_script("""
            // Find the submit button in the listing form
            var forms = document.querySelectorAll('form');
            for (var i = 0; i < forms.length; i++) {
                var form = forms[i];
                
                // Check if this is the listing form
                if (form.querySelector('input[name="txtBrandModel"]')) {
                    var submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(function() {
                            submitBtn.click();
                        }, 1000);
                        return true;
                    }
                }
            }
            return false;
        """)
        
        if submit_clicked:
            print("✅ Submit button clicked!")
        else:
            print("❌ Could not find submit button")
        
        # Wait for result
        print("\n⏳ Waiting for result...")
        time.sleep(8)
        
        # Take final screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"cellpex_complete_final_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        print(f"📸 Final screenshot: {final_screenshot}")
        
        # Check result
        final_url = driver.current_url
        page_content = driver.page_source.lower()
        
        print(f"\n📍 Final URL: {final_url}")
        
        if "success" in page_content or "posted" in page_content:
            print("🎉 SUCCESS! Listing posted!")
        elif "error" in page_content:
            # Find specific errors
            errors = driver.execute_script("""
                var msgs = [];
                var errorElements = document.querySelectorAll('.error, .alert-danger, [class*="error"]');
                errorElements.forEach(function(el) {
                    if (el.textContent.trim()) {
                        msgs.push(el.textContent.trim());
                    }
                });
                return msgs;
            """)
            
            if errors:
                print("⚠️ Validation errors:")
                for err in errors[:5]:  # Show first 5 errors
                    print(f"  - {err}")
            else:
                print("⚠️ Form has errors (check screenshot)")
        else:
            print("📍 Form submitted - check screenshot for result")
        
        # Auto close
        print("\n🤖 Auto-closing in 5 seconds...")
        print(f"📸 Review: {final_screenshot}")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot("cellpex_complete_error.png")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("📋 CELLPEX COMPLETE FORM BOT")
    print("="*50)
    
    success = run_complete_cellpex_listing()
    
    if success:
        print("\n✅ Complete form run finished!")
    else:
        print("\n❌ Complete form run failed!")
    
    sys.exit(0 if success else 1)