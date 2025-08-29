#!/usr/bin/env python3
"""
Final Cellpex Submit - Find and click the actual submit button
"""

import os
import sys
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def run_final_cellpex_submit():
    """Final attempt to submit Cellpex listing with focused approach"""
    
    load_dotenv()
    
    print("🎯 FINAL CELLPEX SUBMIT TEST")
    print("="*50)
    
    # Test data
    listing_data = {
        "category": "Cell Phones",
        "brand": "Apple",
        "model": "iPhone 15 Pro",
        "memory": "128GB",
        "quantity": 2,
        "min_order": 1,
        "price": 999.00,
        "condition": "New",
        "sim_lock": "Unlocked",
        "market_spec": "US Market",
        "carrier": "",
        "packing": "Original Box",
        "incoterm": "FOB",
        "available_date": datetime.now().strftime("%m/%d/%Y"),
        "item_weight": 0.5,
        "description": "Brand new iPhone 15 Pro. Latest model, factory sealed.",
        "remarks": "Fast shipping available"
    }
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        
        # Initialize components
        cellpex_poster = EnhancedCellpexPoster(driver)
        field_mapper = CellpexFieldMapper(driver)
        
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
        
        # Take screenshot before submit
        driver.save_screenshot("cellpex_final_before_submit.png")
        
        # Step 4: Find ALL forms and their submit buttons
        print("\n📍 Step 4: Analyzing ALL forms on page...")
        
        form_analysis = driver.execute_script("""
            var forms = document.querySelectorAll('form');
            var analysis = [];
            
            forms.forEach(function(form, index) {
                var formInfo = {
                    index: index,
                    id: form.id,
                    class: form.className,
                    action: form.action,
                    hasListingFields: false,
                    submitButtons: []
                };
                
                // Check if this form has listing fields
                if (form.querySelector('[name="txtBrandModel"]') || 
                    form.querySelector('[name="txtQuantity"]') ||
                    form.querySelector('[name="areaComments"]')) {
                    formInfo.hasListingFields = true;
                }
                
                // Find all submit elements in this form
                var submitElements = form.querySelectorAll(
                    'input[type="submit"], button[type="submit"], ' +
                    'button:not([type]), input[type="button"], ' +
                    'button[class*="submit"], input[value*="Save"], ' +
                    'input[value*="Submit"]'
                );
                
                submitElements.forEach(function(btn) {
                    if (btn.offsetParent !== null) {
                        formInfo.submitButtons.push({
                            tag: btn.tagName,
                            type: btn.type || 'button',
                            value: btn.value || btn.innerText,
                            id: btn.id,
                            class: btn.className,
                            visible: true
                        });
                    }
                });
                
                // Also check for buttons just outside the form
                var nextElement = form.nextElementSibling;
                while (nextElement && nextElement.tagName !== 'FORM') {
                    if (nextElement.tagName === 'INPUT' || nextElement.tagName === 'BUTTON') {
                        if ((nextElement.type === 'submit' || 
                             nextElement.type === 'button' ||
                             nextElement.value?.includes('Save') ||
                             nextElement.innerText?.includes('Save')) &&
                            nextElement.offsetParent !== null) {
                            formInfo.submitButtons.push({
                                tag: nextElement.tagName,
                                type: nextElement.type,
                                value: nextElement.value || nextElement.innerText,
                                id: nextElement.id,
                                class: nextElement.className,
                                visible: true,
                                outsideForm: true
                            });
                            break;
                        }
                    }
                    nextElement = nextElement.nextElementSibling;
                    if (!nextElement) break;
                }
                
                analysis.push(formInfo);
            });
            
            return analysis;
        """)
        
        print(f"\n📊 Form Analysis:")
        for form in form_analysis:
            print(f"\nForm #{form['index']}:")
            print(f"  - ID: {form.get('id', 'none')}")
            print(f"  - Has listing fields: {form['hasListingFields']}")
            print(f"  - Submit buttons found: {len(form['submitButtons'])}")
            for btn in form['submitButtons']:
                print(f"    • {btn['tag']} - {btn.get('value', btn.get('innerText', 'No text'))}")
        
        # Step 5: Click the submit button in the LISTING form
        print("\n📍 Step 5: Clicking submit button in LISTING form...")
        
        submitted = driver.execute_script("""
            var forms = document.querySelectorAll('form');
            
            // Find the listing form
            for (var i = 0; i < forms.length; i++) {
                var form = forms[i];
                
                if (form.querySelector('[name="txtBrandModel"]')) {
                    console.log('Found listing form at index', i);
                    
                    // Method 1: Look for submit button inside form
                    var submitBtn = form.querySelector(
                        'input[type="submit"], button[type="submit"], ' +
                        'input[value*="Save"], input[value*="Submit"]'
                    );
                    
                    if (submitBtn && submitBtn.offsetParent !== null) {
                        console.log('Found submit button:', submitBtn.outerHTML);
                        submitBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        
                        // Highlight the button
                        submitBtn.style.border = '5px solid green';
                        submitBtn.style.backgroundColor = 'yellow';
                        
                        setTimeout(function() {
                            submitBtn.click();
                            console.log('Clicked submit button');
                        }, 1000);
                        
                        return 'clicked_inside_form';
                    }
                    
                    // Method 2: Look for submit button after form
                    var nextElement = form.nextElementSibling;
                    while (nextElement) {
                        if ((nextElement.tagName === 'INPUT' || nextElement.tagName === 'BUTTON') &&
                            (nextElement.type === 'submit' || 
                             nextElement.value?.includes('Save') ||
                             nextElement.innerText?.includes('Save'))) {
                            
                            console.log('Found submit after form:', nextElement.outerHTML);
                            nextElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                            
                            // Highlight the button
                            nextElement.style.border = '5px solid green';
                            nextElement.style.backgroundColor = 'yellow';
                            
                            setTimeout(function() {
                                nextElement.click();
                                console.log('Clicked submit button after form');
                            }, 1000);
                            
                            return 'clicked_after_form';
                        }
                        
                        if (nextElement.tagName === 'FORM') break;
                        nextElement = nextElement.nextElementSibling;
                    }
                    
                    // Method 3: Submit form directly
                    console.log('No submit button found, submitting form directly');
                    form.submit();
                    return 'form_submitted_directly';
                }
            }
            
            return 'no_listing_form_found';
        """)
        
        print(f"📊 Submit result: {submitted}")
        
        # Wait for submission
        print("\n⏳ Waiting for submission...")
        time.sleep(8)
        
        # Take final screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"cellpex_final_after_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        print(f"📸 Final screenshot: {final_screenshot}")
        
        # Check result
        final_url = driver.current_url
        page_source = driver.page_source.lower()
        
        print(f"\n📍 Final URL: {final_url}")
        
        # Look for success indicators
        if "success" in page_source or "posted" in page_source:
            print("🎉 SUCCESS! Listing posted!")
            return True
        elif "error" in page_source:
            # Extract error messages
            errors = driver.execute_script("""
                var errorElements = document.querySelectorAll(
                    '.error, .alert-danger, .invalid-feedback, ' +
                    '[class*="error"], .text-danger'
                );
                var errors = [];
                errorElements.forEach(function(el) {
                    if (el.textContent.trim()) {
                        errors.push(el.textContent.trim());
                    }
                });
                return errors;
            """)
            
            if errors:
                print("\n❌ Form errors:")
                for error in errors[:5]:
                    print(f"  - {error}")
            else:
                print("⚠️ Possible errors but couldn't extract them")
        else:
            # Check if we're still on the listing page
            if "list/wholesale-inventory" in final_url:
                print("📍 Still on listing page")
                
                # Check if listing was actually created
                if "wholesale-search-results" in driver.current_url:
                    print("✅ Redirected to search results - listing may be created!")
                    return True
            else:
                print("❓ Unknown result - check screenshot")
        
        # Keep browser open for manual inspection
        print("\n🔍 Keeping browser open for 15 seconds...")
        print("👀 Check if listing was created manually")
        time.sleep(15)
        
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            error_screenshot = f"cellpex_final_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🎯 CELLPEX FINAL SUBMIT TEST")
    print("="*50)
    
    success = run_final_cellpex_submit()
    
    if success:
        print("\n✅ Final submit test completed!")
    else:
        print("\n❌ Final submit test failed!")
    
    sys.exit(0 if success else 1)