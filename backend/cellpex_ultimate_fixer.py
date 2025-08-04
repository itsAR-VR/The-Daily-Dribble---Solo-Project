#!/usr/bin/env python3
"""
Cellpex Ultimate Fixer - Uses GPT-4o Mini to actually fix the submission
"""

import os
import sys
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
from enhanced_platform_poster import EnhancedCellpexPoster
from cellpex_field_mapper import CellpexFieldMapper
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class CellpexUltimateFixer:
    """Uses GPT-4o Mini to analyze and fix Cellpex submission"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.wait = WebDriverWait(driver, 20)
    
    def take_screenshot_base64(self):
        """Take screenshot and return as base64"""
        screenshot = self.driver.get_screenshot_as_png()
        return base64.b64encode(screenshot).decode('utf-8')
    
    def analyze_page_state(self, step_description):
        """Use GPT-4o Mini to analyze current page state"""
        
        screenshot_b64 = self.take_screenshot_base64()
        
        # Get page info
        page_info = self.driver.execute_script("""
            return {
                url: window.location.href,
                title: document.title,
                forms: document.querySelectorAll('form').length,
                buttons: document.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                hasListingFields: !!document.querySelector('[name="txtBrandModel"]'),
                pageText: document.body.innerText.substring(0, 500)
            };
        """)
        
        prompt = f"""You are analyzing a Cellpex wholesale inventory listing page. 

CURRENT STEP: {step_description}

PAGE INFO:
- URL: {page_info['url']}
- Title: {page_info['title']}
- Forms on page: {page_info['forms']}
- Buttons on page: {page_info['buttons']}
- Has listing fields: {page_info['hasListingFields']}
- Page text preview: {page_info['pageText'][:200]}...

CONTEXT: I'm building a bot to post wholesale phone listings on Cellpex. The form has been filled with all required fields, but submission is failing.

Based on the screenshot and page info, provide analysis and next actions:

{{
    "page_state": "describe what you see",
    "problem_identified": "what's preventing submission",
    "next_action": "click_button|submit_form|press_enter|navigate|wait|scroll",
    "selector": "CSS selector or XPath if button/element needed",
    "reasoning": "why this action will work",
    "success_indicators": ["what to look for after action"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            print(f"🤖 GPT-4o Mini Analysis: {content}")
            
            # Extract JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "{" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                content = content[json_start:json_end]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ AI Analysis error: {e}")
            return {
                "page_state": "analysis_failed",
                "problem_identified": f"AI error: {e}",
                "next_action": "manual_debug",
                "selector": None,
                "reasoning": "AI analysis failed",
                "success_indicators": []
            }
    
    def execute_action(self, analysis):
        """Execute the action suggested by GPT-4o Mini"""
        
        action = analysis.get("next_action")
        selector = analysis.get("selector")
        
        print(f"🎯 Executing action: {action}")
        if selector:
            print(f"🎯 Using selector: {selector}")
        
        try:
            if action == "click_button" and selector:
                # Find and click button
                if selector.startswith("//"):
                    element = self.driver.find_element(By.XPATH, selector)
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                
                # Highlight it
                self.driver.execute_script("""
                    arguments[0].style.border = '3px solid red';
                    arguments[0].style.backgroundColor = 'yellow';
                """, element)
                
                # Click it
                element.click()
                print(f"✅ Clicked element: {selector}")
                return True
                
            elif action == "submit_form":
                # Submit form directly
                result = self.driver.execute_script("""
                    var forms = document.querySelectorAll('form');
                    for (var i = 0; i < forms.length; i++) {
                        if (forms[i].querySelector('[name="txtBrandModel"]')) {
                            forms[i].submit();
                            return 'submitted';
                        }
                    }
                    return 'no_form_found';
                """)
                print(f"✅ Form submit result: {result}")
                return result == 'submitted'
                
            elif action == "press_enter" and selector:
                # Press enter on specific field
                if selector.startswith("//"):
                    element = self.driver.find_element(By.XPATH, selector)
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.send_keys(Keys.RETURN)
                print(f"✅ Pressed ENTER on: {selector}")
                return True
                
            elif action == "scroll":
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                print("✅ Scrolled to bottom")
                return True
                
            elif action == "wait":
                # Wait for dynamic content
                time.sleep(5)
                print("✅ Waited 5 seconds")
                return True
                
            else:
                print(f"❌ Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"❌ Action failed: {e}")
            return False
    
    def check_success_indicators(self, indicators):
        """Check if success indicators are present"""
        
        if not indicators:
            return False
            
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        
        for indicator in indicators:
            indicator = indicator.lower()
            if (indicator in current_url.lower() or 
                indicator in page_source):
                print(f"✅ Success indicator found: {indicator}")
                return True
        
        return False

def run_ultimate_cellpex_fix():
    """Use GPT-4o Mini to actually fix Cellpex submission"""
    
    load_dotenv()
    
    print("🚀 CELLPEX ULTIMATE FIXER")
    print("="*50)
    print("Using GPT-4o Mini to analyze and fix submission")
    
    # Real listing data
    listing_data = {
        "category": "Cell Phones",
        "brand": "Apple", 
        "model": "iPhone 13 Pro",
        "memory": "512GB",
        "quantity": 3,
        "min_order": 1,
        "price": 699.00,
        "condition": "New",
        "sim_lock": "Unlocked",
        "market_spec": "US Market",
        "carrier": "",
        "packing": "Original Box", 
        "incoterm": "FOB",
        "available_date": datetime.now().strftime("%m/%d/%Y"),
        "item_weight": 0.5,
        "description": "Brand new iPhone 13 Pro 512GB. Factory sealed.",
        "remarks": "Premium device, fast shipping"
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
        fixer = CellpexUltimateFixer(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigate to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        cellpex_poster._dismiss_popups(driver)
        
        # Analyze initial state
        analysis = fixer.analyze_page_state("After navigating to listing page")
        print(f"📊 Initial state: {analysis.get('page_state', 'unknown')}")
        
        # Step 3: Fill form
        print("\n📍 Step 3: Fill form...")
        fill_results = field_mapper.map_and_fill_form(listing_data)
        success_count = sum(1 for v in fill_results.values() if v)
        print(f"✅ Filled {success_count}/{len(fill_results)} fields")
        
        # Step 4: AI-guided submission
        print("\n📍 Step 4: AI-guided submission...")
        
        max_attempts = 5
        attempt = 0
        submitted = False
        
        while attempt < max_attempts and not submitted:
            attempt += 1
            print(f"\n🔄 Attempt {attempt}/{max_attempts}")
            
            # Analyze current state
            analysis = fixer.analyze_page_state(f"Form filled, attempting submission (attempt {attempt})")
            
            print(f"🤖 Problem identified: {analysis.get('problem_identified', 'unknown')}")
            print(f"🎯 Suggested action: {analysis.get('next_action', 'unknown')}")
            
            # Execute the suggested action
            action_success = fixer.execute_action(analysis)
            
            if action_success:
                # Wait for result
                time.sleep(5)
                
                # Check success indicators
                indicators = analysis.get('success_indicators', [])
                if fixer.check_success_indicators(indicators):
                    print("🎉 SUCCESS INDICATORS FOUND!")
                    submitted = True
                    break
                
                # Check if URL changed
                current_url = driver.current_url
                if "list/wholesale-inventory" not in current_url:
                    print(f"🎉 URL CHANGED! New URL: {current_url}")
                    submitted = True
                    break
                    
                # Check for success text
                page_text = driver.page_source.lower()
                success_keywords = ['success', 'posted', 'saved', 'created', 'submitted']
                if any(keyword in page_text for keyword in success_keywords):
                    print("🎉 SUCCESS TEXT FOUND!")
                    submitted = True
                    break
            
            else:
                print("❌ Action failed, trying next approach...")
        
        # Final verification
        print("\n📍 Step 5: Final verification...")
        
        # Take final screenshots
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"cellpex_ultimate_final_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        
        final_url = driver.current_url
        print(f"📍 Final URL: {final_url}")
        print(f"📸 Final screenshot: {final_screenshot}")
        
        if submitted:
            print("\n🎉 LISTING POSTED SUCCESSFULLY!")
            print("🔍 Verifying in account...")
            
            # Navigate to listings to verify
            driver.get("https://www.cellpex.com/my-listings")
            time.sleep(5)
            verification_screenshot = f"cellpex_verification_{timestamp}.png"
            driver.save_screenshot(verification_screenshot)
            print(f"📸 Verification screenshot: {verification_screenshot}")
            
        else:
            print("\n❌ Could not submit listing after 5 attempts")
            
            # Final AI analysis
            final_analysis = fixer.analyze_page_state("Final state after all attempts")
            print(f"🤖 Final AI analysis: {final_analysis.get('problem_identified', 'unknown')}")
        
        # Keep open for verification
        print("\n👀 Keeping browser open for 30 seconds...")
        print("Manually verify the listing in your account!")
        time.sleep(30)
        
        return submitted
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            error_screenshot = f"cellpex_ultimate_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🚀 CELLPEX ULTIMATE FIXER") 
    print("="*50)
    print("⚠️  This WILL post a real listing!")
    print("="*50)
    
    success = run_ultimate_cellpex_fix()
    
    if success:
        print("\n🎉 ULTIMATE SUCCESS!")
        print("The listing has been posted!")
    else:
        print("\n❌ ULTIMATE FAILURE")
        print("Check screenshots and debug further")
    
    sys.exit(0 if success else 1)