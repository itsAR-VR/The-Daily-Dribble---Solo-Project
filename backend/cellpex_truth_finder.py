#!/usr/bin/env python3
"""
Cellpex Truth Finder - No more lies, just facts about what's happening
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def find_the_truth_about_cellpex():
    """Actually figure out what's happening with Cellpex submission"""
    
    load_dotenv()
    
    print("🔍 CELLPEX TRUTH FINDER")
    print("="*50)
    print("No more false claims. Just facts.")
    print("="*50)
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        # Add logging to see what's happening
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        # Initialize components
        cellpex_poster = EnhancedCellpexPoster(driver)
        field_mapper = CellpexFieldMapper(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            print("❌ Login failed")
            return False
        print("✅ Login successful")
        
        # Step 2: Count current listings
        print("\n📍 Step 2: Checking current listings...")
        driver.get("https://www.cellpex.com/my-listings")
        time.sleep(3)
        
        initial_listing_count = len(driver.find_elements(By.CSS_SELECTOR, ".listing-item, .inventory-row, tr.data-row"))
        print(f"📊 Current listings in account: {initial_listing_count}")
        
        # Step 3: Navigate to listing page
        print("\n📍 Step 3: Navigate to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        cellpex_poster._dismiss_popups(driver)
        
        # Step 4: Analyze page structure
        print("\n📍 Step 4: Deep page analysis...")
        
        # Find ALL forms
        forms_analysis = driver.execute_script("""
            const forms = Array.from(document.forms);
            return forms.map((form, idx) => {
                const fields = Array.from(form.elements);
                const buttons = Array.from(form.querySelectorAll(
                    'button, input[type="submit"], input[type="button"]'
                ));
                
                return {
                    index: idx,
                    id: form.id,
                    name: form.name,
                    action: form.action,
                    method: form.method,
                    fieldCount: fields.length,
                    hasListingFields: !!form.querySelector('[name="txtBrandModel"]'),
                    fields: fields.slice(0, 5).map(f => ({
                        name: f.name,
                        type: f.type,
                        required: f.required
                    })),
                    buttons: buttons.map(b => ({
                        type: b.type,
                        value: b.value,
                        text: b.innerText,
                        name: b.name,
                        id: b.id
                    }))
                };
            });
        """)
        
        print(f"\n📊 Found {len(forms_analysis)} forms on page:")
        for form in forms_analysis:
            print(f"\nForm #{form['index']}:")
            print(f"  ID: {form['id']}")
            print(f"  Action: {form['action']}")
            print(f"  Has listing fields: {form['hasListingFields']}")
            print(f"  Buttons: {len(form['buttons'])}")
            if form['buttons']:
                for btn in form['buttons']:
                    print(f"    - {btn['type']}: '{btn['value'] or btn['text']}' (id={btn['id']})")
        
        # Find ALL buttons on page
        all_buttons = driver.execute_script("""
            const buttons = Array.from(document.querySelectorAll(
                'button, input[type="submit"], input[type="button"], a.btn, a.button'
            ));
            return buttons.map(b => ({
                tag: b.tagName,
                type: b.type,
                value: b.value,
                text: b.innerText || b.textContent,
                id: b.id,
                class: b.className,
                onclick: b.onclick ? 'has onclick' : 'no onclick',
                visible: b.offsetParent !== null,
                href: b.href
            })).filter(b => b.visible && 
                (b.value?.toLowerCase().includes('save') ||
                 b.value?.toLowerCase().includes('submit') ||
                 b.value?.toLowerCase().includes('post') ||
                 b.text?.toLowerCase().includes('save') ||
                 b.text?.toLowerCase().includes('submit') ||
                 b.text?.toLowerCase().includes('post')));
        """)
        
        print(f"\n📊 Found {len(all_buttons)} potential submit buttons:")
        for btn in all_buttons:
            print(f"  - {btn['tag']} '{btn['value'] or btn['text']}' (id={btn['id']}, class={btn['class']})")
        
        # Step 5: Fill form with minimal data
        print("\n📍 Step 5: Filling form...")
        test_data = {
            "brand": "Apple",
            "model": "iPhone 13",
            "quantity": 1,
            "price": 500.00,
            "memory": "128GB"
        }
        
        fill_results = field_mapper.map_and_fill_form(test_data)
        filled = sum(1 for v in fill_results.values() if v)
        print(f"✅ Filled {filled}/{len(fill_results)} fields")
        
        # Take screenshot before submit
        driver.save_screenshot("cellpex_truth_before_submit.png")
        print("📸 Pre-submit screenshot saved")
        
        # Step 6: Monitor console and network
        print("\n📍 Step 6: Attempting submission with monitoring...")
        
        # Get initial URL
        initial_url = driver.current_url
        print(f"📍 Initial URL: {initial_url}")
        
        # Try each submit approach
        submit_attempts = [
            {
                "name": "Form-specific submit button",
                "script": """
                    const form = Array.from(document.forms).find(f => 
                        f.querySelector('[name="txtBrandModel"]')
                    );
                    if (form) {
                        const btn = form.querySelector('input[type="submit"], button[type="submit"]');
                        if (btn) {
                            console.log('Clicking form submit button:', btn);
                            btn.click();
                            return 'clicked';
                        }
                    }
                    return 'not_found';
                """
            },
            {
                "name": "Save button by value",
                "script": """
                    const btn = document.querySelector('input[value="Save"], input[value="Submit"]');
                    if (btn) {
                        console.log('Clicking save button:', btn);
                        btn.click();
                        return 'clicked';
                    }
                    return 'not_found';
                """
            },
            {
                "name": "Form submit() method",
                "script": """
                    const form = Array.from(document.forms).find(f => 
                        f.querySelector('[name="txtBrandModel"]')
                    );
                    if (form) {
                        console.log('Submitting form directly');
                        form.submit();
                        return 'submitted';
                    }
                    return 'not_found';
                """
            }
        ]
        
        for attempt in submit_attempts:
            print(f"\n🔄 Trying: {attempt['name']}")
            result = driver.execute_script(attempt['script'])
            print(f"   Result: {result}")
            
            if result != 'not_found':
                # Wait for page change
                time.sleep(5)
                
                # Check what happened
                new_url = driver.current_url
                print(f"   New URL: {new_url}")
                
                # Get console logs
                logs = driver.get_log('browser')
                if logs:
                    print("   Console logs:")
                    for log in logs[-5:]:  # Last 5 logs
                        print(f"     {log['level']}: {log['message']}")
                
                # Check for success indicators
                success_indicators = [
                    "success" in new_url.lower(),
                    "thank" in driver.page_source.lower(),
                    "posted" in driver.page_source.lower(),
                    "created" in driver.page_source.lower(),
                    new_url != initial_url and "search-results" not in new_url
                ]
                
                if any(success_indicators):
                    print("   ✅ Possible success!")
                elif "search-results" in new_url:
                    print("   ❌ FAILED - Redirected to search results (NOT SUCCESS!)")
                else:
                    print("   ❓ Unknown result")
                
                # Take screenshot
                timestamp = datetime.now().strftime("%H%M%S")
                driver.save_screenshot(f"cellpex_truth_attempt_{timestamp}.png")
                
                # Check for errors
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .validation-error")
                if error_elements:
                    print("   ⚠️ Errors found:")
                    for err in error_elements:
                        if err.text:
                            print(f"     - {err.text}")
                
                break
        
        # Step 7: Final verification
        print("\n📍 Step 7: Final verification...")
        time.sleep(5)
        
        final_url = driver.current_url
        print(f"\n📊 FINAL RESULTS:")
        print(f"Initial URL: {initial_url}")
        print(f"Final URL: {final_url}")
        
        if final_url == initial_url:
            print("❌ No navigation occurred - form didn't submit")
        elif "search-results" in final_url:
            print("❌ Navigated to search results - THIS IS NOT SUCCESS!")
        elif "success" in final_url or "thank" in driver.page_source.lower():
            print("✅ Possible success - verification needed")
        else:
            print("❓ Unknown state - manual verification needed")
        
        # Check listing count
        print("\n📍 Checking if listing was actually created...")
        driver.get("https://www.cellpex.com/my-listings")
        time.sleep(3)
        
        final_listing_count = len(driver.find_elements(By.CSS_SELECTOR, ".listing-item, .inventory-row, tr.data-row"))
        print(f"📊 Initial listings: {initial_listing_count}")
        print(f"📊 Final listings: {final_listing_count}")
        
        if final_listing_count > initial_listing_count:
            print("✅ NEW LISTING DETECTED! SUCCESS!")
            return True
        else:
            print("❌ NO NEW LISTING CREATED! FAILURE!")
            return False
        
    except Exception as e:
        print(f"\n❌ Error during truth finding: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot(f"cellpex_truth_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return False
        
    finally:
        if driver:
            # Take final screenshot
            driver.save_screenshot("cellpex_truth_final_state.png")
            # Keep browser open for manual inspection
            print("\n👀 Keeping browser open for 30 seconds for manual inspection...")
            time.sleep(30)
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🔍 CELLPEX TRUTH FINDER")
    print("="*50)
    print("⚠️  This will attempt to post a test listing")
    print("⚠️  And tell you the TRUTH about what happens")
    print("="*50)
    
    success = find_the_truth_about_cellpex()
    
    print("\n" + "="*50)
    print("FINAL VERDICT:")
    if success:
        print("✅ LISTING WAS ACTUALLY CREATED")
    else:
        print("❌ LISTING WAS NOT CREATED")
    print("="*50)
    
    sys.exit(0 if success else 1)