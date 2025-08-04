#!/usr/bin/env python3
"""
Debug Cellpex Form - Inspect the actual HTML
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def debug_cellpex_form():
    """Debug the Cellpex form to find submit button"""
    
    load_dotenv()
    
    print("🔍 CELLPEX FORM DEBUGGER")
    print("="*50)
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        
        # Initialize components
        cellpex_poster = EnhancedCellpexPoster(driver)
        field_mapper = CellpexFieldMapper(driver)
        
        # Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful!")
        
        # Navigate to listing page
        print("\n📍 Step 2: Navigating to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        
        # Dismiss popups
        cellpex_poster._dismiss_popups(driver)
        
        # Fill minimal data
        print("\n📍 Step 3: Filling minimal data...")
        test_data = {
            "brand": "Apple",
            "model": "iPhone 14",
            "quantity": 1,
            "price": 500
        }
        field_mapper.map_and_fill_form(test_data)
        
        # Debug: Find ALL buttons and inputs
        print("\n📍 Step 4: Analyzing page structure...")
        
        # Get all forms
        forms_info = driver.execute_script("""
            var info = [];
            var forms = document.querySelectorAll('form');
            
            forms.forEach(function(form, idx) {
                var formInfo = {
                    index: idx,
                    action: form.action,
                    method: form.method,
                    fields: [],
                    buttons: []
                };
                
                // Get important fields
                ['txtBrandModel', 'txtQuantity', 'txtPrice'].forEach(function(name) {
                    var field = form.querySelector('[name="' + name + '"]');
                    if (field) {
                        formInfo.fields.push(name);
                    }
                });
                
                // Get ALL buttons/submits in and near form
                var allButtons = form.querySelectorAll('input[type="submit"], input[type="button"], button');
                allButtons.forEach(function(btn) {
                    formInfo.buttons.push({
                        tag: btn.tagName,
                        type: btn.type,
                        value: btn.value,
                        text: btn.innerText || btn.value,
                        name: btn.name,
                        id: btn.id,
                        visible: btn.offsetParent !== null
                    });
                });
                
                info.push(formInfo);
            });
            
            return info;
        """)
        
        print("\n📊 Forms found:")
        for form in forms_info:
            print(f"\nForm #{form['index']}:")
            print(f"  Action: {form['action']}")
            print(f"  Method: {form['method']}")
            print(f"  Has listing fields: {len(form['fields']) > 0}")
            print(f"  Fields found: {form['fields']}")
            print(f"  Buttons: {len(form['buttons'])}")
            for btn in form['buttons']:
                if btn['visible']:
                    print(f"    - {btn['tag']} '{btn['text']}' (type={btn['type']}, name={btn['name']}, id={btn['id']})")
        
        # Get buttons outside forms too
        print("\n📍 Looking for buttons outside forms...")
        outside_buttons = driver.execute_script("""
            var buttons = [];
            var allButtons = document.querySelectorAll('input[type="submit"], input[type="button"], button');
            
            allButtons.forEach(function(btn) {
                if (btn.offsetParent !== null && !btn.closest('form')) {
                    buttons.push({
                        tag: btn.tagName,
                        type: btn.type,
                        value: btn.value,
                        text: btn.innerText || btn.value,
                        id: btn.id,
                        class: btn.className,
                        onclick: btn.onclick ? 'has onclick' : 'no onclick'
                    });
                }
            });
            
            return buttons;
        """)
        
        if outside_buttons:
            print("\nButtons outside forms:")
            for btn in outside_buttons:
                print(f"  - {btn['tag']} '{btn['text']}' (id={btn['id']}, class={btn['class']})")
        
        # Take screenshot
        driver.save_screenshot("cellpex_form_debug.png")
        print("\n📸 Debug screenshot saved")
        
        # Try to find submit by looking at page source
        print("\n📍 Searching page source for submit patterns...")
        page_source = driver.page_source
        
        submit_patterns = [
            'type="submit"',
            'type=\'submit\'',
            'value="Save"',
            'value="Submit"',
            'value="Post"',
            'btnSubmit',
            'onclick="submit',
            'form.submit()'
        ]
        
        for pattern in submit_patterns:
            if pattern in page_source:
                print(f"  ✅ Found pattern: {pattern}")
                # Extract context
                idx = page_source.find(pattern)
                context = page_source[max(0, idx-100):idx+100]
                print(f"     Context: ...{context}...")
        
        # Keep browser open
        print("\n👀 Browser staying open for manual inspection...")
        print("Press Ctrl+C to close")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⌨️ Interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    debug_cellpex_form()