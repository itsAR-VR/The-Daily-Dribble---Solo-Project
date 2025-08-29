#!/usr/bin/env python3
"""
Cellpex Honest Bot - No More Hallucinations!
Uses Anti-Hallucination Validator and O4-Mini-High Vision Navigator
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Import our honest components
from backend.anti_hallucination_validator import AntiHallucinationValidator
from backend.o4_mini_high_navigator import O4MiniHighVisionNavigator
from backend.gmail_service import GmailService

# Load environment variables
load_dotenv()


class CellpexHonestBot:
    """
    Cellpex automation bot that tells the truth about submission results.
    No more claiming success when there are validation errors!
    """
    
    def __init__(self, headless: bool = False, verbose: bool = True):
        self.headless = headless
        self.verbose = verbose
        self.driver = None
        
        # Initialize honest components
        self.validator = AntiHallucinationValidator(verbose=verbose)
        self.navigator = O4MiniHighVisionNavigator(verbose=verbose)
        self.gmail_service = GmailService()
        
        # Load credentials
        self.credentials = self._load_credentials()
        
    def _load_credentials(self) -> Dict[str, str]:
        """Load Cellpex credentials from environment"""
        username = os.getenv("CELLPEX_USERNAME")
        password = os.getenv("CELLPEX_PASSWORD")
        
        if not username or not password:
            raise ValueError("CELLPEX_USERNAME and CELLPEX_PASSWORD must be set")
        
        return {"username": username, "password": password}
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        if self.verbose:
            print("✅ Chrome driver initialized")
    
    def login(self) -> bool:
        """Login to Cellpex with 2FA support"""
        try:
            # Navigate to login page
            self.driver.get("https://cellpex.com/login")
            time.sleep(3)
            
            # Fill login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtUser"))
            )
            username_field.clear()
            username_field.send_keys(self.credentials["username"])
            
            password_field = self.driver.find_element(By.ID, "txtPass")
            password_field.clear()
            password_field.send_keys(self.credentials["password"])
            
            # Click login
            login_button = self.driver.find_element(By.ID, "btnLogin")
            login_button.click()
            
            if self.verbose:
                print("🔐 Login credentials submitted")
            
            # Handle 2FA if needed
            time.sleep(5)
            if self._check_for_2fa():
                if not self._handle_2fa():
                    return False
            
            # Verify login success
            return self._verify_login_success()
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def _check_for_2fa(self) -> bool:
        """Check if 2FA page is displayed"""
        try:
            # Look for 2FA indicators
            page_source = self.driver.page_source.lower()
            return any(indicator in page_source for indicator in [
                "verification code", "2fa", "two-factor", "authenticate"
            ])
        except:
            return False
    
    def _handle_2fa(self) -> bool:
        """Handle 2FA verification"""
        try:
            print("📱 2FA required, checking email...")
            
            # Wait for email
            time.sleep(30)
            
            # Search for verification code
            codes = self.gmail_service.search_verification_codes(
                platform="cellpex",
                email_address=self.credentials["username"]
            )
            
            if not codes:
                print("❌ No verification code found")
                return False
            
            code = codes[0]["code"]
            print(f"✅ Found verification code: {code}")
            
            # Enter code
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='number']"))
            )
            code_input.clear()
            code_input.send_keys(code)
            
            # Submit code
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ 2FA handling failed: {e}")
            return False
    
    def _verify_login_success(self) -> bool:
        """Verify successful login"""
        try:
            # Wait for dashboard or inventory page
            WebDriverWait(self.driver, 10).until(
                lambda driver: any(text in driver.current_url for text in ["dashboard", "inventory", "home"])
            )
            
            if self.verbose:
                print(f"✅ Login successful! Current URL: {self.driver.current_url}")
            return True
            
        except:
            print("❌ Login verification failed")
            return False
    
    def navigate_to_listing_form(self) -> bool:
        """Navigate to the listing form using AI guidance"""
        try:
            # Get AI guidance
            analysis = self.navigator.analyze_screenshot(
                self.driver,
                "Navigate to the 'Sell Inventory' or 'List Item' page"
            )
            
            # Try to find and click the sell inventory link
            sell_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Sell")
            if sell_links:
                sell_links[0].click()
                time.sleep(3)
                return True
            
            # Try direct navigation
            self.driver.get("https://cellpex.com/member/sellinventory.php")
            time.sleep(3)
            
            # Verify we're on the listing form
            return "sellinventory" in self.driver.current_url.lower()
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def fill_listing_form(self, listing_data: Dict[str, any]) -> bool:
        """Fill the listing form with AI assistance"""
        try:
            # Dismiss any popups first
            self._dismiss_popups()
            
            # Product Name (Model)
            if "model" in listing_data:
                analysis = self.navigator.analyze_screenshot(
                    self.driver,
                    f"Fill the product/model field with: {listing_data['model']}"
                )
                
                try:
                    model_input = self.driver.find_element(By.ID, "txtBrandModel")
                    model_input.clear()
                    model_input.send_keys(listing_data["model"])
                    
                    # Handle autocomplete
                    time.sleep(2)
                    autocomplete = self.driver.find_elements(By.CSS_SELECTOR, ".ui-menu-item")
                    if autocomplete:
                        autocomplete[0].click()
                        
                except Exception as e:
                    print(f"⚠️  Model field error: {e}")
            
            # Memory
            if "memory" in listing_data:
                try:
                    memory_select = Select(self.driver.find_element(By.NAME, "cmbMemory"))
                    memory_select.select_by_visible_text(listing_data["memory"])
                except:
                    print("⚠️  Memory field not found or failed")
            
            # Condition
            if "condition" in listing_data:
                try:
                    condition_select = Select(self.driver.find_element(By.NAME, "cmbCondition"))
                    condition_select.select_by_visible_text(listing_data["condition"])
                except:
                    print("⚠️  Condition field not found or failed")
            
            # Quantity
            if "quantity" in listing_data:
                try:
                    qty_input = self.driver.find_element(By.NAME, "txtQty")
                    qty_input.clear()
                    qty_input.send_keys(str(listing_data["quantity"]))
                except:
                    print("⚠️  Quantity field not found or failed")
            
            # Price
            if "price" in listing_data:
                try:
                    price_input = self.driver.find_element(By.NAME, "txtPrice")
                    price_input.clear()
                    price_input.send_keys(str(listing_data["price"]))
                except:
                    print("⚠️  Price field not found or failed")
            
            # Comments (using JavaScript for textareas)
            if "comments" in listing_data:
                try:
                    comments = self.driver.find_element(By.NAME, "areaComments")
                    self.driver.execute_script("arguments[0].value = arguments[1];", comments, listing_data["comments"])
                except:
                    print("⚠️  Comments field not found or failed")
            
            return True
            
        except Exception as e:
            print(f"❌ Form filling failed: {e}")
            return False
    
    def _dismiss_popups(self):
        """Dismiss cookie banners and popups"""
        try:
            # Hide cookie banners
            self.driver.execute_script("""
                var popups = document.querySelectorAll('[class*="cookie"], [class*="popup"], [class*="modal"]');
                popups.forEach(function(popup) {
                    popup.style.display = 'none';
                });
            """)
        except:
            pass
    
    def submit_listing(self) -> Tuple[bool, str]:
        """
        Submit the listing and HONESTLY report the result.
        This is where the anti-hallucination magic happens!
        """
        try:
            # Take pre-submission screenshot
            pre_submit_analysis = self.navigator.analyze_screenshot(
                self.driver,
                "Prepare to submit the listing form"
            )
            
            # Find and click submit button
            submit_clicked = False
            
            # Try different submit button selectors
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "#btnSubmit"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                    time.sleep(1)
                    
                    # Try regular click
                    try:
                        submit_btn.click()
                    except:
                        # Fallback to JavaScript click
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                    
                    submit_clicked = True
                    break
                    
                except:
                    continue
            
            if not submit_clicked:
                return False, "Could not find or click submit button"
            
            if self.verbose:
                print("🎯 Submit button clicked")
            
            # Wait for page to respond
            time.sleep(5)
            
            # NOW THE CRITICAL PART - HONEST ANALYSIS!
            post_submit_analysis = self.navigator.analyze_screenshot(
                self.driver,
                "Check if the listing was successfully submitted",
                "Look for success messages, error messages, validation errors, or if we're still on the form"
            )
            
            # Use the anti-hallucination validator
            success = self.validator.is_submission_successful(post_submit_analysis)
            
            # Get detailed verification
            verified_success, reason = self.navigator.verify_submission_success(self.driver)
            
            # Double-check with validator
            if success and not verified_success:
                print("⚠️  Validator and navigator disagree - defaulting to failure")
                success = False
                reason = "Conflicting signals - assuming failure for safety"
            
            # HONEST REPORTING
            if success:
                print("\n✅ VERIFIED SUCCESS - Listing actually submitted!")
                return True, "Listing successfully submitted and verified"
            else:
                print(f"\n❌ HONEST FAILURE DETECTION - {reason}")
                print("📋 The form likely has validation errors or submission was blocked")
                
                # Try to get specific error details
                errors = post_submit_analysis.get("failure_indicators", [])
                warnings = post_submit_analysis.get("warnings", [])
                
                if errors or warnings:
                    print("\n🔍 Specific issues detected:")
                    for error in errors + warnings:
                        print(f"  - {error}")
                
                return False, f"Submission failed: {reason}"
            
        except Exception as e:
            print(f"❌ Submit error: {e}")
            return False, f"Exception during submission: {str(e)}"
    
    def create_listing(self, listing_data: Dict[str, any]) -> bool:
        """
        Complete listing creation process with HONEST reporting
        """
        try:
            # Setup driver
            self.setup_driver()
            
            # Login
            if not self.login():
                print("❌ Login failed")
                return False
            
            # Navigate to listing form
            if not self.navigate_to_listing_form():
                print("❌ Could not navigate to listing form")
                return False
            
            # Fill form
            if not self.fill_listing_form(listing_data):
                print("❌ Form filling failed")
                return False
            
            # Submit with HONEST result reporting
            success, message = self.submit_listing()
            
            print(f"\n{'='*60}")
            print(f"📊 FINAL RESULT: {'SUCCESS' if success else 'FAILURE'}")
            print(f"💬 Details: {message}")
            print(f"{'='*60}")
            
            # Keep browser open for verification if failed
            if not success and not self.headless:
                print("\n👀 Keeping browser open for 30 seconds for inspection...")
                time.sleep(30)
            
            return success
            
        except Exception as e:
            print(f"❌ Listing creation error: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_session_summary(self) -> Dict[str, any]:
        """Get summary of the session"""
        return {
            "validator_summary": self.validator.get_validation_summary(),
            "navigator_summary": self.navigator.get_summary(),
            "timestamp": datetime.now().isoformat()
        }


# Test the honest bot
if __name__ == "__main__":
    print("🤖 CELLPEX HONEST BOT - NO MORE HALLUCINATIONS!")
    print("="*60)
    
    # Test data
    test_listing = {
        "model": "Apple iPhone 15 Pro",
        "memory": "128GB",
        "condition": "Used",
        "quantity": "1",
        "price": "899.99",
        "comments": "Excellent condition, minor scratches",
        "remarks": "Original box included"
    }
    
    # Create bot
    bot = CellpexHonestBot(headless=False, verbose=True)
    
    print("\n📋 Test Listing Data:")
    print(json.dumps(test_listing, indent=2))
    
    print("\n🚀 Starting honest listing process...")
    print("This bot will tell the TRUTH about submission results!\n")
    
    # Run the bot
    success = bot.create_listing(test_listing)
    
    # Get session summary
    summary = bot.get_session_summary()
    
    print("\n📊 Session Summary:")
    print(f"Validations performed: {summary['validator_summary']['total']}")
    print(f"Failures caught: {summary['validator_summary']['failures']}")
    print(f"Screenshots taken: {summary['navigator_summary']['screenshots_taken']}")
    
    if not success:
        print("\n💡 Tips for fixing submission failures:")
        print("1. Check all required fields are filled")
        print("2. Ensure product model matches autocomplete options")
        print("3. Verify price format is correct")
        print("4. Check for any validation error messages")
    
    print("\n✅ Honest bot session complete!")
"""
Cellpex Honest Bot - No More Hallucinations!
Uses Anti-Hallucination Validator and O4-Mini-High Vision Navigator
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Import our honest components
from backend.anti_hallucination_validator import AntiHallucinationValidator
from backend.o4_mini_high_navigator import O4MiniHighVisionNavigator
from backend.gmail_service import GmailService

# Load environment variables
load_dotenv()


class CellpexHonestBot:
    """
    Cellpex automation bot that tells the truth about submission results.
    No more claiming success when there are validation errors!
    """
    
    def __init__(self, headless: bool = False, verbose: bool = True):
        self.headless = headless
        self.verbose = verbose
        self.driver = None
        
        # Initialize honest components
        self.validator = AntiHallucinationValidator(verbose=verbose)
        self.navigator = O4MiniHighVisionNavigator(verbose=verbose)
        self.gmail_service = GmailService()
        
        # Load credentials
        self.credentials = self._load_credentials()
        
    def _load_credentials(self) -> Dict[str, str]:
        """Load Cellpex credentials from environment"""
        username = os.getenv("CELLPEX_USERNAME")
        password = os.getenv("CELLPEX_PASSWORD")
        
        if not username or not password:
            raise ValueError("CELLPEX_USERNAME and CELLPEX_PASSWORD must be set")
        
        return {"username": username, "password": password}
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        if self.verbose:
            print("✅ Chrome driver initialized")
    
    def login(self) -> bool:
        """Login to Cellpex with 2FA support"""
        try:
            # Navigate to login page
            self.driver.get("https://cellpex.com/login")
            time.sleep(3)
            
            # Fill login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtUser"))
            )
            username_field.clear()
            username_field.send_keys(self.credentials["username"])
            
            password_field = self.driver.find_element(By.ID, "txtPass")
            password_field.clear()
            password_field.send_keys(self.credentials["password"])
            
            # Click login
            login_button = self.driver.find_element(By.ID, "btnLogin")
            login_button.click()
            
            if self.verbose:
                print("🔐 Login credentials submitted")
            
            # Handle 2FA if needed
            time.sleep(5)
            if self._check_for_2fa():
                if not self._handle_2fa():
                    return False
            
            # Verify login success
            return self._verify_login_success()
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def _check_for_2fa(self) -> bool:
        """Check if 2FA page is displayed"""
        try:
            # Look for 2FA indicators
            page_source = self.driver.page_source.lower()
            return any(indicator in page_source for indicator in [
                "verification code", "2fa", "two-factor", "authenticate"
            ])
        except:
            return False
    
    def _handle_2fa(self) -> bool:
        """Handle 2FA verification"""
        try:
            print("📱 2FA required, checking email...")
            
            # Wait for email
            time.sleep(30)
            
            # Search for verification code
            codes = self.gmail_service.search_verification_codes(
                platform="cellpex",
                email_address=self.credentials["username"]
            )
            
            if not codes:
                print("❌ No verification code found")
                return False
            
            code = codes[0]["code"]
            print(f"✅ Found verification code: {code}")
            
            # Enter code
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='number']"))
            )
            code_input.clear()
            code_input.send_keys(code)
            
            # Submit code
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ 2FA handling failed: {e}")
            return False
    
    def _verify_login_success(self) -> bool:
        """Verify successful login"""
        try:
            # Wait for dashboard or inventory page
            WebDriverWait(self.driver, 10).until(
                lambda driver: any(text in driver.current_url for text in ["dashboard", "inventory", "home"])
            )
            
            if self.verbose:
                print(f"✅ Login successful! Current URL: {self.driver.current_url}")
            return True
            
        except:
            print("❌ Login verification failed")
            return False
    
    def navigate_to_listing_form(self) -> bool:
        """Navigate to the listing form using AI guidance"""
        try:
            # Get AI guidance
            analysis = self.navigator.analyze_screenshot(
                self.driver,
                "Navigate to the 'Sell Inventory' or 'List Item' page"
            )
            
            # Try to find and click the sell inventory link
            sell_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "Sell")
            if sell_links:
                sell_links[0].click()
                time.sleep(3)
                return True
            
            # Try direct navigation
            self.driver.get("https://cellpex.com/member/sellinventory.php")
            time.sleep(3)
            
            # Verify we're on the listing form
            return "sellinventory" in self.driver.current_url.lower()
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def fill_listing_form(self, listing_data: Dict[str, any]) -> bool:
        """Fill the listing form with AI assistance"""
        try:
            # Dismiss any popups first
            self._dismiss_popups()
            
            # Product Name (Model)
            if "model" in listing_data:
                analysis = self.navigator.analyze_screenshot(
                    self.driver,
                    f"Fill the product/model field with: {listing_data['model']}"
                )
                
                try:
                    model_input = self.driver.find_element(By.ID, "txtBrandModel")
                    model_input.clear()
                    model_input.send_keys(listing_data["model"])
                    
                    # Handle autocomplete
                    time.sleep(2)
                    autocomplete = self.driver.find_elements(By.CSS_SELECTOR, ".ui-menu-item")
                    if autocomplete:
                        autocomplete[0].click()
                        
                except Exception as e:
                    print(f"⚠️  Model field error: {e}")
            
            # Memory
            if "memory" in listing_data:
                try:
                    memory_select = Select(self.driver.find_element(By.NAME, "cmbMemory"))
                    memory_select.select_by_visible_text(listing_data["memory"])
                except:
                    print("⚠️  Memory field not found or failed")
            
            # Condition
            if "condition" in listing_data:
                try:
                    condition_select = Select(self.driver.find_element(By.NAME, "cmbCondition"))
                    condition_select.select_by_visible_text(listing_data["condition"])
                except:
                    print("⚠️  Condition field not found or failed")
            
            # Quantity
            if "quantity" in listing_data:
                try:
                    qty_input = self.driver.find_element(By.NAME, "txtQty")
                    qty_input.clear()
                    qty_input.send_keys(str(listing_data["quantity"]))
                except:
                    print("⚠️  Quantity field not found or failed")
            
            # Price
            if "price" in listing_data:
                try:
                    price_input = self.driver.find_element(By.NAME, "txtPrice")
                    price_input.clear()
                    price_input.send_keys(str(listing_data["price"]))
                except:
                    print("⚠️  Price field not found or failed")
            
            # Comments (using JavaScript for textareas)
            if "comments" in listing_data:
                try:
                    comments = self.driver.find_element(By.NAME, "areaComments")
                    self.driver.execute_script("arguments[0].value = arguments[1];", comments, listing_data["comments"])
                except:
                    print("⚠️  Comments field not found or failed")
            
            return True
            
        except Exception as e:
            print(f"❌ Form filling failed: {e}")
            return False
    
    def _dismiss_popups(self):
        """Dismiss cookie banners and popups"""
        try:
            # Hide cookie banners
            self.driver.execute_script("""
                var popups = document.querySelectorAll('[class*="cookie"], [class*="popup"], [class*="modal"]');
                popups.forEach(function(popup) {
                    popup.style.display = 'none';
                });
            """)
        except:
            pass
    
    def submit_listing(self) -> Tuple[bool, str]:
        """
        Submit the listing and HONESTLY report the result.
        This is where the anti-hallucination magic happens!
        """
        try:
            # Take pre-submission screenshot
            pre_submit_analysis = self.navigator.analyze_screenshot(
                self.driver,
                "Prepare to submit the listing form"
            )
            
            # Find and click submit button
            submit_clicked = False
            
            # Try different submit button selectors
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "#btnSubmit"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                    time.sleep(1)
                    
                    # Try regular click
                    try:
                        submit_btn.click()
                    except:
                        # Fallback to JavaScript click
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                    
                    submit_clicked = True
                    break
                    
                except:
                    continue
            
            if not submit_clicked:
                return False, "Could not find or click submit button"
            
            if self.verbose:
                print("🎯 Submit button clicked")
            
            # Wait for page to respond
            time.sleep(5)
            
            # NOW THE CRITICAL PART - HONEST ANALYSIS!
            post_submit_analysis = self.navigator.analyze_screenshot(
                self.driver,
                "Check if the listing was successfully submitted",
                "Look for success messages, error messages, validation errors, or if we're still on the form"
            )
            
            # Use the anti-hallucination validator
            success = self.validator.is_submission_successful(post_submit_analysis)
            
            # Get detailed verification
            verified_success, reason = self.navigator.verify_submission_success(self.driver)
            
            # Double-check with validator
            if success and not verified_success:
                print("⚠️  Validator and navigator disagree - defaulting to failure")
                success = False
                reason = "Conflicting signals - assuming failure for safety"
            
            # HONEST REPORTING
            if success:
                print("\n✅ VERIFIED SUCCESS - Listing actually submitted!")
                return True, "Listing successfully submitted and verified"
            else:
                print(f"\n❌ HONEST FAILURE DETECTION - {reason}")
                print("📋 The form likely has validation errors or submission was blocked")
                
                # Try to get specific error details
                errors = post_submit_analysis.get("failure_indicators", [])
                warnings = post_submit_analysis.get("warnings", [])
                
                if errors or warnings:
                    print("\n🔍 Specific issues detected:")
                    for error in errors + warnings:
                        print(f"  - {error}")
                
                return False, f"Submission failed: {reason}"
            
        except Exception as e:
            print(f"❌ Submit error: {e}")
            return False, f"Exception during submission: {str(e)}"
    
    def create_listing(self, listing_data: Dict[str, any]) -> bool:
        """
        Complete listing creation process with HONEST reporting
        """
        try:
            # Setup driver
            self.setup_driver()
            
            # Login
            if not self.login():
                print("❌ Login failed")
                return False
            
            # Navigate to listing form
            if not self.navigate_to_listing_form():
                print("❌ Could not navigate to listing form")
                return False
            
            # Fill form
            if not self.fill_listing_form(listing_data):
                print("❌ Form filling failed")
                return False
            
            # Submit with HONEST result reporting
            success, message = self.submit_listing()
            
            print(f"\n{'='*60}")
            print(f"📊 FINAL RESULT: {'SUCCESS' if success else 'FAILURE'}")
            print(f"💬 Details: {message}")
            print(f"{'='*60}")
            
            # Keep browser open for verification if failed
            if not success and not self.headless:
                print("\n👀 Keeping browser open for 30 seconds for inspection...")
                time.sleep(30)
            
            return success
            
        except Exception as e:
            print(f"❌ Listing creation error: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_session_summary(self) -> Dict[str, any]:
        """Get summary of the session"""
        return {
            "validator_summary": self.validator.get_validation_summary(),
            "navigator_summary": self.navigator.get_summary(),
            "timestamp": datetime.now().isoformat()
        }


# Test the honest bot
if __name__ == "__main__":
    print("🤖 CELLPEX HONEST BOT - NO MORE HALLUCINATIONS!")
    print("="*60)
    
    # Test data
    test_listing = {
        "model": "Apple iPhone 15 Pro",
        "memory": "128GB",
        "condition": "Used",
        "quantity": "1",
        "price": "899.99",
        "comments": "Excellent condition, minor scratches",
        "remarks": "Original box included"
    }
    
    # Create bot
    bot = CellpexHonestBot(headless=False, verbose=True)
    
    print("\n📋 Test Listing Data:")
    print(json.dumps(test_listing, indent=2))
    
    print("\n🚀 Starting honest listing process...")
    print("This bot will tell the TRUTH about submission results!\n")
    
    # Run the bot
    success = bot.create_listing(test_listing)
    
    # Get session summary
    summary = bot.get_session_summary()
    
    print("\n📊 Session Summary:")
    print(f"Validations performed: {summary['validator_summary']['total']}")
    print(f"Failures caught: {summary['validator_summary']['failures']}")
    print(f"Screenshots taken: {summary['navigator_summary']['screenshots_taken']}")
    
    if not success:
        print("\n💡 Tips for fixing submission failures:")
        print("1. Check all required fields are filled")
        print("2. Ensure product model matches autocomplete options")
        print("3. Verify price format is correct")
        print("4. Check for any validation error messages")
    
    print("\n✅ Honest bot session complete!")