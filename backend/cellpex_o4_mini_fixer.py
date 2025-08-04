#!/usr/bin/env python3
"""
Cellpex o4-mini Fixer - Uses o4-mini reasoning model via Responses API
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

class CellpexO4MiniFixer:
    """Uses o4-mini reasoning model via Responses API"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.wait = WebDriverWait(driver, 20)
        self.reasoning_context = []  # Store reasoning items for better performance
    
    def take_screenshot_base64(self):
        """Take screenshot and return as base64"""
        screenshot = self.driver.get_screenshot_as_png()
        return base64.b64encode(screenshot).decode('utf-8')
    
    def analyze_with_o4_mini(self, step_description, screenshot_b64):
        """Use o4-mini reasoning model to analyze page state"""
        
        # Get page info
        page_info = self.driver.execute_script("""
            return {
                url: window.location.href,
                title: document.title,
                forms: document.querySelectorAll('form').length,
                buttons: document.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                hasListingFields: !!document.querySelector('[name="txtBrandModel"]'),
                pageText: document.body.innerText.substring(0, 300),
                visibleButtons: Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'))
                    .filter(btn => btn.offsetParent !== null)
                    .map(btn => ({
                        tag: btn.tagName,
                        type: btn.type,
                        value: btn.value,
                        text: btn.innerText || btn.textContent || btn.value,
                        name: btn.name,
                        id: btn.id,
                        className: btn.className
                    }))
            };
        """)
        
        # Build the input context
        input_context = self.reasoning_context.copy()  # Include previous reasoning
        input_context.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""You are analyzing a Cellpex wholesale inventory listing page to help submit a listing.

CURRENT STEP: {step_description}

PAGE ANALYSIS:
- URL: {page_info['url']}
- Title: {page_info['title']}
- Forms: {page_info['forms']}
- Total buttons: {page_info['buttons']}
- Has listing fields: {page_info['hasListingFields']}
- Page text: {page_info['pageText'][:200]}...

VISIBLE BUTTONS:
{json.dumps(page_info['visibleButtons'], indent=2)}

CONTEXT: I'm building a bot to post wholesale phone listings on Cellpex. The form has been filled with all required fields, but submission is failing. I need to identify exactly which button to click to submit the listing.

IMPORTANT: Look at the screenshot carefully. The form is already filled. I need to find the correct submit button for the LISTING FORM (not search forms or other buttons).

Provide a JSON response with your reasoning and action:
{{
    "page_analysis": "describe what you see in detail",
    "form_status": "filled|partially_filled|empty|error",
    "submit_button_identified": true/false,
    "recommended_action": "click_button|submit_form|scroll|wait|navigate",
    "button_selector": "exact CSS selector or XPath if button found",
    "button_description": "description of the button to click",
    "confidence": "high|medium|low",
    "reasoning": "detailed explanation of why this action will work",
    "alternative_actions": ["backup actions if primary fails"]
}}"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_b64}",
                        "detail": "high"
                    }
                }
            ]
        })
        
        try:
            # Use o4-mini via Responses API
            response = self.client.responses.create(
                model="o4-mini",
                input=input_context,
                reasoning={"effort": "high"},  # Use high reasoning effort
                max_output_tokens=1000,
                temperature=0.1
            )
            
            # Store reasoning items for next call (improves performance)
            self.reasoning_context.extend(response.output)
            
            # Extract the text response
            response_text = None
            for output_item in response.output:
                if hasattr(output_item, 'content') and output_item.content:
                    for content_item in output_item.content:
                        if hasattr(content_item, 'text'):
                            response_text = content_item.text
                            break
                    if response_text:
                        break
            
            if not response_text:
                response_text = response.output_text if hasattr(response, 'output_text') else str(response.output[-1])
            
            print(f"🧠 o4-mini Analysis: {response_text[:500]}...")
            
            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_content = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_content = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            analysis = json.loads(json_content)
            
            # Show reasoning usage
            if hasattr(response, 'usage'):
                reasoning_tokens = response.usage.output_tokens_details.reasoning_tokens if hasattr(response.usage, 'output_tokens_details') else 0
                print(f"🧠 Reasoning tokens used: {reasoning_tokens}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ o4-mini Analysis error: {e}")
            return {
                "page_analysis": "analysis_failed",
                "form_status": "unknown",
                "submit_button_identified": False,
                "recommended_action": "manual_debug",
                "button_selector": None,
                "button_description": "AI analysis failed",
                "confidence": "low",
                "reasoning": f"o4-mini error: {e}",
                "alternative_actions": ["try_manual_submission"]
            }
    
    def execute_o4_action(self, analysis):
        """Execute the action recommended by o4-mini"""
        
        action = analysis.get("recommended_action")
        selector = analysis.get("button_selector")
        confidence = analysis.get("confidence", "low")
        
        print(f"🎯 o4-mini recommends: {action} (confidence: {confidence})")
        if selector:
            print(f"🎯 Target selector: {selector}")
        
        try:
            if action == "click_button" and selector:
                # Find and click the button
                if selector.startswith("//"):
                    element = self.driver.find_element(By.XPATH, selector)
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                
                # Highlight it
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid lime';
                    arguments[0].style.backgroundColor = 'yellow';
                    arguments[0].style.boxShadow = '0 0 20px lime';
                """, element)
                
                # Take screenshot of highlighted element
                self.driver.save_screenshot(f"o4_mini_target_{datetime.now().strftime('%H%M%S')}.png")
                
                # Try multiple click methods
                try:
                    element.click()
                    print("✅ Standard click successful")
                    return True
                except:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        print("✅ JavaScript click successful")
                        return True
                    except:
                        try:
                            # Force click even if intercepted
                            self.driver.execute_script("""
                                arguments[0].dispatchEvent(new MouseEvent('click', {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true
                                }));
                            """, element)
                            print("✅ Force click successful")
                            return True
                        except Exception as e:
                            print(f"❌ All click methods failed: {e}")
                            return False
                
            elif action == "submit_form":
                # Submit form directly
                result = self.driver.execute_script("""
                    var forms = document.querySelectorAll('form');
                    for (var i = 0; i < forms.length; i++) {
                        if (forms[i].querySelector('[name="txtBrandModel"]')) {
                            forms[i].submit();
                            return 'submitted_listing_form';
                        }
                    }
                    // Try any form if listing form not found
                    if (forms.length > 0) {
                        forms[0].submit();
                        return 'submitted_first_form';
                    }
                    return 'no_forms_found';
                """)
                print(f"✅ Form submission result: {result}")
                return result in ['submitted_listing_form', 'submitted_first_form']
                
            elif action == "scroll":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                print("✅ Scrolled to bottom")
                return True
                
            elif action == "wait":
                time.sleep(5)
                print("✅ Waited 5 seconds")
                return True
                
            else:
                print(f"❌ Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"❌ Action execution failed: {e}")
            return False
    
    def check_submission_success(self):
        """Check if the listing was successfully submitted"""
        
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        
        # Success indicators
        success_patterns = [
            "success",
            "posted",
            "saved", 
            "created",
            "submitted",
            "thank you",
            "confirmation",
            "listing added",
            "inventory added"
        ]
        
        # URL change indicators
        url_indicators = [
            "wholesale-search-results",
            "my-listings", 
            "inventory-list",
            "confirmation",
            "success"
        ]
        
        # Check URL change
        if any(indicator in current_url.lower() for indicator in url_indicators):
            print(f"✅ URL changed to success page: {current_url}")
            return True
            
        # Check page content
        if any(pattern in page_source for pattern in success_patterns):
            print("✅ Success text found in page")
            return True
            
        # Check if still on listing page (could be error)
        if "list/wholesale-inventory" in current_url:
            print("⚠️ Still on listing page - check for errors")
            return False
            
        return False

def run_o4_mini_cellpex_fix():
    """Use o4-mini reasoning model to fix Cellpex submission"""
    
    load_dotenv()
    
    print("🧠 CELLPEX o4-MINI FIXER")
    print("="*50)
    print("Using o4-mini reasoning model via Responses API")
    
    # Test listing data
    listing_data = {
        "category": "Cell Phones",
        "brand": "Apple",
        "model": "iPhone 14 Pro Max", 
        "memory": "1TB",
        "quantity": 1,
        "min_order": 1,
        "price": 1199.00,
        "condition": "New",
        "sim_lock": "Unlocked",
        "market_spec": "US Market",
        "carrier": "",
        "packing": "Original Box",
        "incoterm": "FOB", 
        "available_date": datetime.now().strftime("%m/%d/%Y"),
        "item_weight": 0.5,
        "description": "Brand new iPhone 14 Pro Max 1TB. Factory sealed, original packaging.",
        "remarks": "Premium device, immediate shipping available"
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
        o4_fixer = CellpexO4MiniFixer(driver)
        
        # Step 1: Login
        print("\n📍 Step 1: Login with 2FA...")
        if not cellpex_poster.login_with_2fa():
            return False
        print("✅ Login successful!")
        
        # Step 2: Navigate to listing page
        print("\n📍 Step 2: Navigate to listing page...")
        driver.get("https://www.cellpex.com/list/wholesale-inventory")
        time.sleep(5)
        cellpex_poster._dismiss_popups(driver)
        
        # Step 3: Fill form
        print("\n📍 Step 3: Fill form...")
        fill_results = field_mapper.map_and_fill_form(listing_data)
        success_count = sum(1 for v in fill_results.values() if v)
        print(f"✅ Filled {success_count}/{len(fill_results)} fields")
        
        # Step 4: o4-mini powered submission
        print("\n📍 Step 4: o4-mini powered analysis and submission...")
        
        max_attempts = 3
        attempt = 0
        submitted = False
        
        while attempt < max_attempts and not submitted:
            attempt += 1
            print(f"\n🧠 o4-mini Attempt {attempt}/{max_attempts}")
            
            # Take screenshot for analysis
            screenshot_b64 = o4_fixer.take_screenshot_base64()
            
            # Analyze with o4-mini
            analysis = o4_fixer.analyze_with_o4_mini(
                f"Form filled, attempting submission (attempt {attempt})", 
                screenshot_b64
            )
            
            print(f"📊 Form status: {analysis.get('form_status', 'unknown')}")
            print(f"🎯 Submit button found: {analysis.get('submit_button_identified', False)}")
            print(f"🧠 Reasoning: {analysis.get('reasoning', 'none')[:100]}...")
            
            # Execute the recommended action
            action_success = o4_fixer.execute_o4_action(analysis)
            
            if action_success:
                # Wait for result
                time.sleep(8)
                
                # Check for success
                if o4_fixer.check_submission_success():
                    print("🎉 SUBMISSION SUCCESS DETECTED!")
                    submitted = True
                    break
                else:
                    print("⚠️ No success detected, continuing...")
            else:
                print("❌ Action failed, trying alternatives...")
                
                # Try alternative actions
                alternatives = analysis.get('alternative_actions', [])
                for alt_action in alternatives:
                    print(f"🔄 Trying alternative: {alt_action}")
                    if alt_action == "try_manual_submission":
                        # Force submit any form
                        result = driver.execute_script("""
                            var forms = document.querySelectorAll('form');
                            if (forms.length > 0) {
                                forms[0].submit();
                                return true;
                            }
                            return false;
                        """)
                        if result:
                            time.sleep(5)
                            if o4_fixer.check_submission_success():
                                submitted = True
                                break
        
        # Final verification
        print("\n📍 Step 5: Final verification...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"cellpex_o4_final_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        
        final_url = driver.current_url
        print(f"📍 Final URL: {final_url}")
        print(f"📸 Final screenshot: {final_screenshot}")
        
        if submitted:
            print("\n🎉 LISTING SUCCESSFULLY SUBMITTED!")
            print("🔍 Verifying in account...")
            
            # Navigate to verify
            driver.get("https://www.cellpex.com/my-listings")
            time.sleep(5)
            verification_screenshot = f"cellpex_o4_verification_{timestamp}.png"
            driver.save_screenshot(verification_screenshot)
            print(f"📸 Verification screenshot: {verification_screenshot}")
            
        else:
            print("\n❌ Could not submit listing after all attempts")
            
            # Final o4-mini analysis of failure
            screenshot_b64 = o4_fixer.take_screenshot_base64()
            final_analysis = o4_fixer.analyze_with_o4_mini("Final state - submission failed", screenshot_b64)
            print(f"🧠 Final o4-mini diagnosis: {final_analysis.get('reasoning', 'unknown')}")
        
        # Keep browser open for manual verification
        print("\n👀 Keeping browser open for 30 seconds for manual verification...")
        time.sleep(30)
        
        return submitted
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            error_screenshot = f"cellpex_o4_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
            
        return False
        
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*50)
    print("🧠 CELLPEX o4-MINI REASONING FIXER")
    print("="*50)
    print("⚠️  This WILL post a real listing!")
    print("Uses o4-mini reasoning model via Responses API")
    print("="*50)
    
    success = run_o4_mini_cellpex_fix()
    
    if success:
        print("\n🎉 o4-MINI SUCCESS!")
        print("Listing posted using reasoning model!")
    else:
        print("\n❌ o4-MINI UNABLE TO SUBMIT")
        print("Check screenshots and debug further")
    
    sys.exit(0 if success else 1)