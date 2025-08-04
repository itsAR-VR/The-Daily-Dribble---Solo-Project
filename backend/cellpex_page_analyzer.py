#!/usr/bin/env python3
"""
Cellpex Page Analyzer - Find out what's ACTUALLY on the page
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def analyze_cellpex_page():
    """Analyze what's actually on the Cellpex listing page"""
    
    load_dotenv()
    
    print("🔬 CELLPEX PAGE ANALYZER")
    print("="*50)
    print("Finding what's ACTUALLY on the page")
    print("="*50)
    
    driver = None
    
    try:
        # Setup browser
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        # Initialize poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigate to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Analyze ALL form elements
        print("\n📍 Step 3: Analyzing ALL form elements...")
        
        # Get all input elements
        all_inputs = driver.execute_script("""
            const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
            return inputs.map(el => ({
                tag: el.tagName,
                type: el.type,
                name: el.name,
                id: el.id,
                class: el.className,
                placeholder: el.placeholder,
                value: el.value,
                visible: el.offsetParent !== null,
                required: el.required,
                disabled: el.disabled,
                readonly: el.readOnly,
                formId: el.form ? el.form.id : null,
                options: el.tagName === 'SELECT' ? 
                    Array.from(el.options).map(opt => ({
                        value: opt.value,
                        text: opt.text,
                        selected: opt.selected
                    })) : null
            }));
        """)
        
        print(f"\n📊 Found {len(all_inputs)} form elements total")
        
        # Group by visibility
        visible_inputs = [inp for inp in all_inputs if inp['visible']]
        hidden_inputs = [inp for inp in all_inputs if not inp['visible']]
        
        print(f"✅ Visible: {len(visible_inputs)}")
        print(f"❌ Hidden: {len(hidden_inputs)}")
        
        # Analyze visible elements
        print("\n🔍 VISIBLE FORM ELEMENTS:")
        for inp in visible_inputs:
            print(f"\n{inp['tag']} - {inp['name'] or inp['id'] or 'unnamed'}")
            print(f"  Type: {inp['type']}")
            print(f"  ID: {inp['id']}")
            print(f"  Class: {inp['class'][:50]}...")
            print(f"  Required: {inp['required']}")
            print(f"  Disabled: {inp['disabled']}")
            print(f"  Form: {inp['formId']}")
            
            if inp['tag'] == 'SELECT' and inp['options']:
                print(f"  Options: {len(inp['options'])} choices")
                # Show first 3 options
                for i, opt in enumerate(inp['options'][:3]):
                    print(f"    - '{opt['text']}' (value={opt['value']})")
                if len(inp['options']) > 3:
                    print(f"    ... and {len(inp['options']) - 3} more")
        
        # Step 4: Check for dynamic behavior
        print("\n📍 Step 4: Testing dynamic behavior...")
        
        # Try selecting first dropdown to see if it reveals more fields
        selects = driver.find_elements(By.TAG_NAME, "select")
        if selects:
            first_visible_select = None
            for sel in selects:
                if sel.is_displayed():
                    first_visible_select = sel
                    break
            
            if first_visible_select:
                print(f"\n🔄 Found visible select: {first_visible_select.get_attribute('name')}")
                
                # Get options
                from selenium.webdriver.support.ui import Select
                select_obj = Select(first_visible_select)
                options = select_obj.options
                
                if len(options) > 1:
                    # Select second option (first is usually placeholder)
                    print(f"  Selecting: '{options[1].text}'")
                    select_obj.select_by_index(1)
                    time.sleep(2)
                    
                    # Check if new fields appeared
                    new_visible = driver.execute_script("""
                        return Array.from(document.querySelectorAll('input, select, textarea'))
                            .filter(el => el.offsetParent !== null).length;
                    """)
                    
                    print(f"  Visible fields after selection: {new_visible} (was {len(visible_inputs)})")
                    
                    if new_visible > len(visible_inputs):
                        print("  ✅ New fields appeared! Form is dynamic.")
                    else:
                        print("  ❌ No new fields. Form might be static.")
        
        # Step 5: Find ALL buttons
        print("\n📍 Step 5: Finding ALL buttons...")
        
        all_buttons = driver.execute_script("""
            const buttons = Array.from(document.querySelectorAll(
                'button, input[type="button"], input[type="submit"], a.btn, a[class*="button"]'
            ));
            return buttons.map(btn => ({
                tag: btn.tagName,
                type: btn.type,
                text: btn.innerText || btn.value || btn.textContent,
                id: btn.id,
                name: btn.name,
                class: btn.className,
                visible: btn.offsetParent !== null,
                href: btn.href,
                onclick: btn.onclick ? 'has onclick' : null,
                formId: btn.form ? btn.form.id : null,
                position: btn.offsetParent ? {
                    top: btn.offsetTop,
                    left: btn.offsetLeft
                } : null
            })).filter(btn => btn.visible);
        """)
        
        print(f"\n📊 Found {len(all_buttons)} visible buttons:")
        for btn in all_buttons:
            print(f"\n{btn['tag']} - '{btn['text']}'")
            print(f"  ID: {btn['id']}")
            print(f"  Type: {btn['type']}")
            print(f"  Form: {btn['formId']}")
            print(f"  Position: {btn['position']}")
        
        # Step 6: Check page structure
        print("\n📍 Step 6: Checking page structure...")
        
        page_info = driver.execute_script("""
            return {
                title: document.title,
                forms: document.forms.length,
                iframes: document.querySelectorAll('iframe').length,
                scripts: Array.from(document.scripts).filter(s => s.src.includes('cellpex')).length,
                hasJQuery: typeof jQuery !== 'undefined',
                hasAngular: typeof angular !== 'undefined',
                hasReact: !!document.querySelector('[data-reactroot]'),
                bodyClasses: document.body.className
            };
        """)
        
        print(f"\n📊 Page info:")
        for key, value in page_info.items():
            print(f"  {key}: {value}")
        
        # Take screenshots
        driver.save_screenshot("cellpex_page_analysis.png")
        print("\n📸 Analysis screenshot saved")
        
        # Save full analysis to file
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "visible_inputs": visible_inputs,
            "buttons": all_buttons,
            "page_info": page_info
        }
        
        with open("cellpex_page_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        print("📄 Full analysis saved to cellpex_page_analysis.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot(f"cellpex_analysis_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return False
        
    finally:
        if driver:
            print("\n👀 Keeping browser open for 30 seconds...")
            time.sleep(30)
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🔬 CELLPEX PAGE ANALYZER") 
    print("="*50)
    
    success = analyze_cellpex_page()
    
    if success:
        print("\n✅ Analysis complete!")
        print("Check cellpex_page_analysis.json for details")
    else:
        print("\n❌ Analysis failed")
    
    sys.exit(0 if success else 1)