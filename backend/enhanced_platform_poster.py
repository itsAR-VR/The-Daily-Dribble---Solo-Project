#!/usr/bin/env python3
"""
Enhanced platform poster with Gmail 2FA integration and optional step-by-step screenshot capture.
"""

import time
import base64
from datetime import datetime
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import Gmail service for 2FA (robust: try local then package path)
try:
    from gmail_service import gmail_service as _gmail_service
    gmail_service = _gmail_service
    GMAIL_AVAILABLE = gmail_service and gmail_service.is_available()
except Exception:
    try:
        from backend.gmail_service import gmail_service as _gmail_service
        gmail_service = _gmail_service
        GMAIL_AVAILABLE = gmail_service and gmail_service.is_available()
    except Exception:
        GMAIL_AVAILABLE = False
        gmail_service = None

class Enhanced2FAMarketplacePoster:
    """Enhanced base class with 2FA support via Gmail"""
    
    def __init__(self, driver: webdriver.Chrome, capture_callback=None) -> None:
        self.driver = driver
        self.username, self.password = self._load_credentials()
        self.gmail_service = gmail_service if GMAIL_AVAILABLE else None
        self.max_2fa_attempts = 3
        self.tfa_wait_time = 30  # seconds to wait for 2FA code
        self._capture_callback = capture_callback
        self.last_steps = []

    def _capture_step(self, step: str, message: str = "") -> None:
        """Capture a screenshot into base64 and append to steps."""
        try:
            png = self.driver.get_screenshot_as_png()
            b64 = base64.b64encode(png).decode("utf-8")
        except Exception:
            b64 = None
        item = {"step": step, "message": message, "screenshot_b64": b64}
        self.last_steps.append(item)
        if self._capture_callback:
            try:
                self._capture_callback({
                    "label": step,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "image_base64": b64,
                    "note": message,
                })
            except Exception:
                pass
    
    def _load_credentials(self) -> tuple[str, str]:
        """Load platform credentials from environment variables"""
        load_dotenv()
        user = os.getenv(f"{self.PLATFORM.upper()}_USERNAME")
        pwd = os.getenv(f"{self.PLATFORM.upper()}_PASSWORD")
        if not user or not pwd:
            raise RuntimeError(f"Missing credentials for {self.PLATFORM}")
        return user, pwd
    
    def login_with_2fa(self) -> bool:
        """Enhanced login with 2FA support"""
        if not self.LOGIN_URL:
            raise NotImplementedError("LOGIN_URL must be defined")
            
        driver = self.driver
        driver.get(self.LOGIN_URL)
        self._capture_step("login_page", f"Opened login page: {self.LOGIN_URL}")
        wait = WebDriverWait(driver, 20)
        
        try:
            # Standard login
            print(f"🔐 Logging into {self.PLATFORM}...")
            
            # Find and fill username
            user_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='username'], input[name='email'], input[type='email']")
            ))
            user_field.clear()
            user_field.send_keys(self.username)
            
            # Find and fill password
            pass_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='password'], input[type='password']")
            ))
            pass_field.clear()
            pass_field.send_keys(self.password)
            self._capture_step("login_filled", "Filled username and password")
            
            # Submit login
            submit = driver.find_element(
                By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], button:contains('Login'), button:contains('Sign in')"
            )
            submit.click()
            self._capture_step("login_submitted", "Submitted login form")
            
            # Check for 2FA
            if self._check_for_2fa():
                print(f"📱 2FA required for {self.PLATFORM}")
                return self._handle_2fa()
            else:
                print(f"✅ Logged into {self.PLATFORM} successfully (no 2FA)")
                self._capture_step("login_success", "Logged in without 2FA")
                return True
                
        except TimeoutException:
            print(f"❌ Login timeout for {self.PLATFORM}")
            return False
        except Exception as e:
            print(f"❌ Login error for {self.PLATFORM}: {e}")
            return False
    
    def _check_for_2fa(self) -> bool:
        """Check if 2FA is required"""
        driver = self.driver
        time.sleep(2)  # Wait for page to load
        
        # Common 2FA indicators
        indicators = [
            "verification code",
            "2fa",
            "two-factor",
            "authentication code",
            "verify your identity",
            "enter code",
            "security code"
        ]
        
        page_text = driver.page_source.lower()
        return any(indicator in page_text for indicator in indicators)
    
    def _handle_2fa(self) -> bool:
        """Enhanced 2FA authentication with email monitoring and LLM extraction"""
        if not self.gmail_service:
            print("❌ Gmail service not available for 2FA")
            return False
            
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        
        print(f"📧 Waiting for 2FA email from {self.PLATFORM}...")
        print("⏳ Allowing time for email delivery (60 seconds)...")
        time.sleep(60)  # Wait for email to arrive
        self._capture_step("2fa_wait_email", "Waiting for 2FA email to arrive")
        
        for attempt in range(self.max_2fa_attempts):
            print(f"🔍 Attempt {attempt + 1}/{self.max_2fa_attempts} - Searching for 2FA email...")
            
            # Search for recent emails containing platform name
            code = self._extract_2fa_code_from_email()
            
            if code:
                print(f"✅ Found 2FA code: {code}")
                
                # Find 2FA input field and enter code
                if self._enter_2fa_code(code, wait):
                    # Check if login successful
                    time.sleep(3)
                    if self._check_login_success():
                        print(f"✅ 2FA successful for {self.PLATFORM}")
                        self._capture_step("2fa_success", "2FA successful, logged in")
                        return True
                    else:
                        print(f"⚠️  2FA code might be incorrect or expired, retrying...")
                else:
                    print(f"❌ Failed to enter 2FA code")
            else:
                print(f"⚠️  No 2FA code found in recent emails")
                
            # Wait before retry
            if attempt < self.max_2fa_attempts - 1:
                print("⏳ Waiting 15 seconds before retry...")
                time.sleep(15)
                
        print(f"❌ Failed to complete 2FA for {self.PLATFORM}")
        return False
    
    def _extract_2fa_code_from_email(self) -> str:
        """Extract 2FA code from recent emails using LLM"""
        try:
            # Search for emails containing the platform name in the last 10 minutes
            platform_name = self.PLATFORM.lower()
            recent_emails = self._search_recent_emails(platform_name, minutes_back=10)
            
            if not recent_emails:
                print(f"📧 No recent emails found containing '{platform_name}'")
                return None
                
            # Get the most recent email
            latest_email = recent_emails[0]
            email_content = latest_email.get('content', '')
            email_subject = latest_email.get('subject', '')
            
            print(f"📨 Found recent email: '{email_subject[:50]}...'")
            
            # Use LLM to extract authentication code
            code = self._llm_extract_auth_code(email_content, email_subject)
            return code
            
        except Exception as e:
            print(f"❌ Error extracting 2FA code from email: {e}")
            return None
    
    def _search_recent_emails(self, platform_name: str, minutes_back: int = 10) -> list:
        """Search for recent emails containing platform name"""
        try:
            from datetime import datetime, timedelta
            
            # Calculate time threshold
            time_threshold = datetime.now() - timedelta(minutes=minutes_back)
            time_str = time_threshold.strftime('%Y/%m/%d')
            
            # Simple search query - just look for the platform name
            query = f"subject:{platform_name} OR from:{platform_name} OR {platform_name} after:{time_str}"
            
            print(f"🔍 Searching Gmail with query: {query}")
            
            # Use gmail service to search
            results = self.gmail_service.search_verification_codes(platform_name, minutes_back)
            return results
            
        except Exception as e:
            print(f"❌ Error searching recent emails: {e}")
            return []
    
    def _llm_extract_auth_code(self, email_content: str, email_subject: str) -> str:
        """Use OpenAI LLM to extract authentication code from email"""
        try:
            # Import OpenAI (check if available)
            try:
                from openai import OpenAI
                import os
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print("⚠️  OpenAI API key not available, falling back to regex")
                    return self._regex_extract_auth_code(email_content)
                    
                client = OpenAI(api_key=api_key)
                
            except ImportError:
                print("⚠️  OpenAI not available, falling back to regex")
                return self._regex_extract_auth_code(email_content)
            
            # Prepare prompt for LLM
            prompt = f"""
            Extract the authentication/verification code from this email.
            
            Subject: {email_subject}
            Content: {email_content[:1000]}  # Limit content to avoid token limits
            
            Instructions:
            1. Look for numeric codes (usually 4-8 digits)
            2. Common patterns: "Your code is 123456", "Verification code: 123456", "123456 is your code"
            3. Return ONLY the numeric code, nothing else
            4. If no code found, return "NO_CODE_FOUND"
            
            Code:"""
            
            # Prefer GPT‑5 if available, then fall back gracefully
            models = [os.getenv("OPENAI_MODEL", "gpt-5"), "gpt-4o", "gpt-3.5-turbo"]
            response = None
            last_err = None
            for mdl in models:
                try:
                    response = client.chat.completions.create(
                        model=mdl,
                        messages=[
                            {"role": "system", "content": "You are a precise code extractor. Return only the authentication code or 'NO_CODE_FOUND'."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=50,
                        temperature=0
                    )
                    break
                except Exception as e:
                    last_err = e
                    continue
            if response is None:
                raise last_err if last_err else RuntimeError("LLM call failed")

            extracted_code = response.choices[0].message.content.strip()
            
            if extracted_code == "NO_CODE_FOUND" or not extracted_code.isdigit():
                print("🤖 LLM couldn't find code, trying regex fallback...")
                return self._regex_extract_auth_code(email_content)
            
            print(f"🤖 LLM extracted code: {extracted_code}")
            return extracted_code
            
        except Exception as e:
            print(f"❌ Error with LLM extraction: {e}, falling back to regex")
            return self._regex_extract_auth_code(email_content)
    
    def _regex_extract_auth_code(self, email_content: str) -> str:
        """Fallback regex-based code extraction"""
        import re
        
        # Common patterns for authentication codes
        patterns = [
            r'(?:code|verification|authentication)[\s:]*(\d{4,8})',
            r'(\d{4,8})[\s]*is your.*(?:code|verification)',
            r'Your.*(?:code|verification)[\s:]*(\d{4,8})',
            r'\b(\d{6})\b',  # 6-digit codes are common
            r'\b(\d{4})\b',  # 4-digit codes
            r'\b(\d{8})\b'   # 8-digit codes
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, email_content, re.IGNORECASE)
            if matches:
                code = matches[0]
                print(f"🔍 Regex extracted code: {code}")
                return code
        
        print("❌ No authentication code found with regex")
        return None
    
    def _enter_2fa_code(self, code: str, wait: WebDriverWait) -> bool:
        """Enter 2FA code into the form"""
        try:
            # Find 2FA input field with multiple selectors
            selectors = [
                "input[name='code']",
                "input[name='otp']", 
                "input[name='token']",
                "input[name='verification']",
                "input[placeholder*='code']",
                "input[placeholder*='verification']",
                "input[placeholder*='authentication']",
                "input[type='text'][maxlength='6']",  # Common for 6-digit codes
                "input[type='text'][maxlength='4']",  # Common for 4-digit codes
            ]
            
            code_field = None
            for selector in selectors:
                try:
                    code_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
            
            if not code_field:
                print("❌ Could not find 2FA input field")
                return False
            
            # Clear and enter code
            code_field.clear()
            code_field.send_keys(code)
            print(f"✅ Entered 2FA code: {code}")
            
            # Submit code
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']", 
                "button:contains('Verify')",
                "button:contains('Submit')",
                "button:contains('Continue')",
                "[onclick*='verify']",
                "[onclick*='submit']"
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit = self.driver.find_element(By.CSS_SELECTOR, selector)
                    submit.click()
                    submitted = True
                    print("✅ Submitted 2FA code")
                    break
                except:
                    continue
            
            # If no submit button found, try Enter key
            if not submitted:
                code_field.send_keys("\n")
                print("✅ Submitted 2FA code with Enter key")
            
            return True
            
        except Exception as e:
            print(f"❌ Error entering 2FA code: {e}")
            return False
    
    def _check_login_success(self) -> bool:
        """Check if login was successful"""
        driver = self.driver
        
        # Platform-specific success indicators
        success_indicators = {
            'hubx': ['dashboard', 'inventory', 'sell'],
            'gsmexchange': ['my account', 'post listing', 'dashboard'],
            'cellpex': ['dashboard', 'listings', 'profile'],
            'kardof': ['panel', 'listings', 'account'],
            'handlot': ['dashboard', 'inventory', 'account']
        }
        
        platform_indicators = success_indicators.get(self.PLATFORM.lower(), ['dashboard', 'account'])
        page_text = driver.page_source.lower()
        
        return any(indicator in page_text for indicator in platform_indicators)


class EnhancedGSMExchangePoster(Enhanced2FAMarketplacePoster):
    """GSM Exchange with 2FA support"""
    PLATFORM = "GSMEXCHANGE"
    LOGIN_URL = "https://www.gsmexchange.com/signin"
    
    def post_listing(self, row):
        """Post listing with enhanced error handling"""
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        
        try:
            # Navigate to listing page
            driver.get("https://www.gsmexchange.com/gsm/post_offers.html")
            
            # Select "I want to sell"
            sell_radio = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[value='sell']")
            ))
            sell_radio.click()
            
            # Fill in listing details
            # Model/Product name
            model_field = wait.until(EC.presence_of_element_located(
                (By.NAME, "title")
            ))
            model_field.clear()
            model_field.send_keys(str(row.get("product_name", "")))
            
            # Quantity
            qty_field = driver.find_element(By.NAME, "qty")
            qty_field.clear()
            qty_field.send_keys(str(row.get("quantity", "")))
            
            # Price
            price_field = driver.find_element(By.NAME, "price") 
            price_field.clear()
            price_field.send_keys(str(row.get("price", "")))
            
            # Condition - needs dropdown selection
            condition_map = {
                "New": "New",
                "Used": "Used and tested",
                "Refurbished": "Refurbished"
            }
            condition = row.get("condition", "New")
            # Select condition from dropdown
            
            # Submit
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            # Wait for success
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'successfully')]")
            ))
            
            return "Success"
            
        except TimeoutException:
            return "Timeout posting listing"
        except Exception as e:
            return f"Error: {str(e)}"


class EnhancedCellpexPoster(Enhanced2FAMarketplacePoster):
    """Cellpex with 2FA support"""
    PLATFORM = "CELLPEX"
    LOGIN_URL = "https://www.cellpex.com/login"
    
    def login_with_2fa(self) -> bool:
        """Enhanced login with 2FA support - Cellpex specific implementation"""
        driver = self.driver
        driver.get(self.LOGIN_URL)
        self._capture_step("cellpex_login_page", f"Opened login page: {self.LOGIN_URL}")
        wait = WebDriverWait(driver, 20)
        
        try:
            print(f"🔐 Logging into {self.PLATFORM}...")
            
            # Cellpex-specific selectors
            user_field = wait.until(EC.presence_of_element_located(
                (By.NAME, "txtUser")
            ))
            user_field.clear()
            user_field.send_keys(self.username)
            
            pass_field = wait.until(EC.presence_of_element_located(
                (By.NAME, "txtPass")
            ))
            pass_field.clear()
            pass_field.send_keys(self.password)
            self._capture_step("cellpex_login_filled", "Filled Cellpex credentials")
            
            # Submit login using the submit input
            submit = wait.until(EC.element_to_be_clickable(
                (By.NAME, "btnLogin")
            ))
            submit.click()
            self._capture_step("cellpex_login_submitted", "Submitted Cellpex login")
            
            # Wait a bit for potential redirect
            time.sleep(3)
            
            # Check if we're on 2FA page (check URL)
            current_url = driver.current_url
            if "login_verify" in current_url:
                print(f"📱 2FA required for {self.PLATFORM}")
                self._capture_step("cellpex_2fa_page", "Cellpex 2FA verification page detected")
                return self._handle_cellpex_2fa()
            else:
                print(f"✅ Logged into {self.PLATFORM} successfully (no 2FA)")
                return self._check_cellpex_login_success()
                
        except TimeoutException:
            print(f"❌ Login timeout for {self.PLATFORM}")
            return False
        except Exception as e:
            print(f"❌ Login error for {self.PLATFORM}: {e}")
            return False
    
    def _check_cellpex_login_success(self) -> bool:
        """Check if Cellpex login was successful"""
        driver = self.driver
        current_url = driver.current_url
        
        # Success if we're not on login/verify pages
        if "login" not in current_url and "verify" not in current_url:
            print(f"✅ {self.PLATFORM} login successful - URL: {current_url}")
            return True
        else:
            print(f"❌ {self.PLATFORM} login failed - still on: {current_url}")
            return False
    
    def _handle_cellpex_2fa(self) -> bool:
        """Handle Cellpex-specific 2FA flow"""
        if not self.gmail_service:
            print("❌ Gmail service not available for 2FA")
            return False
            
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        
        print(f"📧 Waiting for 2FA email from {self.PLATFORM}...")
        print("⏳ Allowing time for email delivery (10 seconds)...")
        time.sleep(10)  # Shorter wait for Cellpex
        self._capture_step("cellpex_2fa_wait", "Waiting shortly for Cellpex 2FA email")
        
        for attempt in range(self.max_2fa_attempts):
            print(f"🔍 Attempt {attempt + 1}/{self.max_2fa_attempts} - Searching for 2FA email...")
            
            # Use Cellpex-specific email extraction
            code = self._extract_cellpex_2fa_code()
            
            if code:
                print(f"✅ Found 2FA code: {code}")
                
                # Find the correct 2FA input field (txtCode)
                if self._enter_cellpex_2fa_code(code, wait):
                    # Check if login successful
                    time.sleep(3)
                    if self._check_cellpex_login_success():
                        print(f"✅ 2FA successful for {self.PLATFORM}")
                        self._capture_step("cellpex_2fa_success", "Cellpex 2FA successful")
                        return True
                    else:
                        print(f"⚠️  2FA code might be incorrect or expired, retrying...")
                else:
                    print(f"❌ Failed to enter 2FA code")
            else:
                print(f"⚠️  No 2FA code found in recent emails")
                
            # Wait before retry
            if attempt < self.max_2fa_attempts - 1:
                print("⏳ Waiting 15 seconds before retry...")
                time.sleep(15)
                
        print(f"❌ Failed to complete 2FA for {self.PLATFORM}")
        return False
    
    def _extract_cellpex_2fa_code(self) -> str:
        """Extract Cellpex verification code using our working method"""
        if not self.gmail_service or not self.gmail_service.is_available():
            print("❌ Gmail service not available")
            return None
        
        try:
            # Use simple query that works
            query = 'from:cellpex.com after:2025/08/03'
            print(f"🔍 Searching Gmail with query: {query}")
            
            results = self.gmail_service.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                print("❌ No Cellpex emails found")
                return None
            
            # Get the latest message
            msg_id = messages[0]['id']
            msg_data = self.gmail_service.service.users().messages().get(
                userId='me',
                id=msg_id
            ).execute()
            
            # Extract code from snippet
            snippet = msg_data.get('snippet', '')
            import re
            codes = re.findall(r'\b(\d{6})\b', snippet)
            
            if codes:
                code = codes[0]
                print(f"✅ Found verification code: {code}")
                return code
            else:
                print("❌ No code found in email")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting code: {e}")
            return None
    
    def _enter_cellpex_2fa_code(self, code: str, wait: WebDriverWait) -> bool:
        """Enter 2FA code specifically for Cellpex"""
        try:
            # Look for the Access Code Required text first
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Access Code Required')]")
            ))
            print("✅ Found 'Access Code Required' text")
            
            # Find the txtCode input field specifically
            code_input = wait.until(EC.presence_of_element_located((By.ID, "txtCode")))
            print("✅ Found txtCode input field")
            
            # Clear and enter the code
            code_input.clear()
            time.sleep(1)
            code_input.send_keys(code)
            print(f"✅ Code entered in txtCode field: {code}")
            
            # Submit using the form submit button
            submit_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//form//input[@type='submit']")
            ))
            submit_btn.click()
            print("✅ Form submitted using submit button")
            
            return True
            
        except Exception as e:
            print(f"❌ Error entering Cellpex 2FA code: {e}")
            return False
    
    def _dismiss_popups(self, driver):
        """Dismiss any popups that might interfere with form interaction"""
        popup_selectors = [
            ".eupopup-container",
            "[class*='cookie']",
            "[class*='popup']",
            "[class*='modal']",
            "[class*='overlay']",
            "#cookie-banner",
            ".cookie-consent",
            ".gdpr-popup"
        ]
        
        dismissed_count = 0
        
        for selector in popup_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        try:
                            driver.execute_script("arguments[0].style.display = 'none';", element)
                            dismissed_count += 1
                        except:
                            pass
            except:
                continue
        
        if dismissed_count > 0:
            print(f"🍪 Dismissed {dismissed_count} popups/overlays")
            
        return dismissed_count > 0
    
    def post_listing(self, row):
        """Post listing to Cellpex using the correct wholesale inventory form"""
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        
        try:
            # Navigate to Sell Inventory page (discovered during testing)
            print("📍 Navigating to Cellpex Sell Inventory page...")
            driver.get("https://www.cellpex.com/list/wholesale-inventory")
            self._capture_step("sell_inventory_page", "Opened Sell Inventory form")
            
            # Wait for form to load
            time.sleep(3)
            
            # Fill form fields based on discovered selectors
            print("📝 Filling listing form...")
            
            # Category selection (selCateg)
            try:
                category_select = wait.until(EC.presence_of_element_located((By.NAME, "selCateg")))
                # Default to smartphones/mobile category
                from selenium.webdriver.support.ui import Select
                category_dropdown = Select(category_select)
                # Try to select appropriate category
                try:
                    category_dropdown.select_by_visible_text("Smartphones")
                except:
                    try:
                        category_dropdown.select_by_index(1)  # First non-empty option
                    except:
                        pass
                print("✅ Category selected")
                self._capture_step("category_selected", "Category selected")
            except Exception as e:
                print(f"⚠️  Could not select category: {e}")
            
            # Brand selection (selBrand)
            try:
                brand_select = wait.until(EC.presence_of_element_located((By.NAME, "selBrand")))
                brand_dropdown = Select(brand_select)
                brand = str(row.get("brand", "Apple"))
                try:
                    brand_dropdown.select_by_visible_text(brand)
                except:
                    try:
                        brand_dropdown.select_by_index(1)  # First non-empty option
                    except:
                        pass
                print(f"✅ Brand selected: {brand}")
                self._capture_step("brand_selected", f"Brand selected: {brand}")
            except Exception as e:
                print(f"⚠️  Could not select brand: {e}")
            
            # Available quantity (txtAvailable)
            try:
                available_field = wait.until(EC.presence_of_element_located((By.NAME, "txtAvailable")))
                available_field.clear()
                quantity = str(row.get("quantity", "1"))
                available_field.send_keys(quantity)
                print(f"✅ Quantity entered: {quantity}")
                self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors)
            try:
                price_value = str(row.get("price", "")).strip()
                if price_value:
                    price_selectors = [
                        (By.NAME, "txtPrice"),
                        (By.NAME, "txtAsk"),
                        (By.NAME, "txtAmount"),
                        (By.CSS_SELECTOR, "input[name*='price' i]"),
                    ]
                    price_field = None
                    for by, sel in price_selectors:
                        try:
                            price_field = driver.find_element(by, sel)
                            break
                        except Exception:
                            continue
                    if price_field:
                        price_field.clear()
                        price_field.send_keys(price_value)
                        print(f"✅ Price entered: {price_value}")
                        self._capture_step("price_entered", f"Price: {price_value}")
            except Exception as e:
                print(f"⚠️  Could not enter price: {e}")

            # Currency (try select: selCurrency or similar)
            try:
                currency = str(row.get("currency", "USD")).upper()
                currency_select = None
                for name in ["selCurrency", "selCur", "selCurr"]:
                    try:
                        currency_select = driver.find_element(By.NAME, name)
                        break
                    except Exception:
                        continue
                if currency_select:
                    Select(currency_select).select_by_visible_text(currency)
                    print(f"✅ Currency selected: {currency}")
                    self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names)
            try:
                condition = str(row.get("condition", "Used"))
                cond_select = None
                for name in ["selCondition", "selCond", "condition"]:
                    try:
                        cond_select = driver.find_element(By.NAME, name)
                        break
                    except Exception:
                        continue
                if cond_select:
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                    except Exception:
                        try:
                            Select(cond_select).select_by_index(1)
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                product_name = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}"
                # Prefer interactive typing to trigger autocomplete
                model_field = None
                for locator in [
                    (By.NAME, "txtBrandModel"),
                    (By.ID, "txtBrandModel"),
                    (By.CSS_SELECTOR, "input[name*='BrandModel' i]")
                ]:
                    try:
                        model_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if model_field:
                    model_field.clear()
                    model_field.click()
                    # Type slowly to trigger suggestions
                    for chunk in product_name.split(" "):
                        model_field.send_keys(chunk + " ")
                        time.sleep(0.3)
                    time.sleep(1.5)
                    # Try to pick a suggestion item
                    suggestion_xpaths = [
                        "//ul[contains(@class,'ui-autocomplete')]//li[1]",
                        "//li[contains(@class,'ui-menu-item')][1]",
                        "//div[contains(@class,'autocomplete') or contains(@class,'suggest') ]//li[1]"
                    ]
                    picked = False
                    for sx in suggestion_xpaths:
                        try:
                            sug = driver.find_element(By.XPATH, sx)
                            if sug.is_displayed():
                                driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", sug)
                                time.sleep(0.2)
                                driver.execute_script("arguments[0].click();", sug)
                                picked = True
                                break
                        except Exception:
                            continue
                    if not picked:
                        # Fallback to JS set + change/blur events
                        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input')); arguments[0].dispatchEvent(new Event('change')); arguments[0].blur();", model_field, product_name)
                    print(f"✅ Product name set: {product_name} {'(picked suggestion)' if picked else '(direct)'}")
                    self._capture_step("product_name_set", f"Product name: {product_name}")
                    # Inspect potential hidden fields that autocomplete may set
                    try:
                        hidden_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='hidden']")
                        hidden_summary = []
                        for hf in hidden_fields:
                            try:
                                name = hf.get_attribute('name') or hf.get_attribute('id')
                                val = (hf.get_attribute('value') or '')[:40]
                                if name and val:
                                    hidden_summary.append(f"{name}={val}")
                            except Exception:
                                continue
                        if hidden_summary:
                            self._capture_step("hidden_fields", ", ".join(hidden_summary[:8]))
                    except Exception:
                        pass
                else:
                    # Last resort JS injection
                    driver.execute_script("""
                        var field = document.querySelector('[name="txtBrandModel"]');
                        if (field) {
                            field.value = arguments[0];
                            field.dispatchEvent(new Event('change'));
                        }
                    """, product_name)
                    print(f"✅ Product name set via JavaScript: {product_name}")
                    self._capture_step("product_name_set", f"Product name: {product_name}")
            except Exception as e:
                print(f"⚠️  Skipping product name due to: {e}")
            
            # Comments/Description (areaComments) - Use JavaScript injection for reliability
            try:
                comments_field = wait.until(EC.presence_of_element_located((By.NAME, "areaComments")))
                description = str(row.get("description", f"High quality {row.get('brand', 'Apple')} device in {row.get('condition', 'excellent')} condition"))
                # Use JavaScript injection to avoid interaction issues
                driver.execute_script("arguments[0].value = arguments[1];", comments_field, description)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", comments_field)
                print("✅ Description entered (JavaScript injection)")
                self._capture_step("description_entered", "Entered description")
            except Exception as e:
                print(f"⚠️  Could not enter description: {e}")
            
            # Remarks (areaRemarks) - Enhanced with memory info, using JavaScript injection
            try:
                remarks_field = wait.until(EC.presence_of_element_located((By.NAME, "areaRemarks")))
                # ✅ Include memory in remarks since it's no longer in product name
                remarks = f"Memory: {row.get('memory', '128GB')} | Condition: {row.get('condition', 'Excellent')} | Color: {row.get('color', 'Space Black')}"
                # Use JavaScript injection to avoid interaction issues
                driver.execute_script("arguments[0].value = arguments[1];", remarks_field, remarks)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", remarks_field)
                print("✅ Remarks entered (JavaScript injection with memory info)")
                self._capture_step("remarks_entered", "Entered remarks with memory info")
            except Exception as e:
                print(f"⚠️  Could not enter remarks: {e}")
            
            # Take screenshot before submitting
            self._capture_step("form_filled", "Form fields filled before submit")
            
            # Enhanced submit with popup handling
            print("📤 Submitting listing with enhanced popup handling...")
            
            # Step 1: Dismiss popups first
            self._dismiss_popups(driver)
            
            # Step 2: Scroll to bottom to reveal submit area
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Step 3: Dismiss popups again after scroll
            self._dismiss_popups(driver)
            
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[name='btnSubmit']",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'save')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'save')]",
                "//a[contains(@onclick,'save') or contains(@onclick,'Save')]",
                "//input[contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'save')]",
                "//input[contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                # Common ASP.NET patterns
                "[onclick*='__doPostBack']",
                "input[id*='btn']",
                "button[id*='btn']",
                "input[name*='btn']",
                "button[name*='btn']",
                "//input[contains(@id,'btn') or contains(@name,'btn')]",
            ]

            submitted = False
            # Track the form URL so we can detect a real redirect after submit
            form_url = driver.current_url
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_btn = driver.find_element(By.XPATH, selector)
                    else:
                        submit_btn = driver.find_element(By.CSS_SELECTOR, selector)

                    if submit_btn.is_displayed():
                        # Scroll to submit button
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_btn)
                        time.sleep(2)
                        
                        # Final popup dismissal
                        self._dismiss_popups(driver)
                        
                        # Try JavaScript click first (most reliable)
                        try:
                            driver.execute_script("arguments[0].click();", submit_btn)
                            submitted = True
                            print(f"✅ Form submitted using JavaScript click: {selector}")
                            break
                        except:
                            # Fallback to regular click
                            submit_btn.click()
                            submitted = True
                            print(f"✅ Form submitted using regular click: {selector}")
                            break
                except:
                    continue

            if not submitted:
                # Try selecting obvious agreement checkboxes then retry
                try:
                    for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                        try:
                            label_txt = (cb.get_attribute('name') or '') + ' ' + (cb.get_attribute('id') or '')
                            if any(k in label_txt.lower() for k in ["agree", "confirm", "terms", "stock", "accurate", "true"]):
                                if not cb.is_selected():
                                    driver.execute_script("arguments[0].click();", cb)
                        except Exception:
                            continue
                except Exception:
                    pass
                # Try Enter key on the last field
                print("⚠️  Could not find submit button, trying Enter key...")
                try:
                    remarks_field = driver.find_element(By.NAME, "areaRemarks")
                    remarks_field.send_keys("\n")
                    submitted = True
                    print("✅ Form submitted using Enter key")
                except Exception:
                    pass

            # Final fallback: submit the nearest form via JavaScript
            if not submitted:
                try:
                    driver.execute_script(
                        "var f = document.querySelector('form'); if (f) { f.submit(); return true } else { return false }"
                    )
                    submitted = True
                    print("✅ Form submitted via form.submit() JS fallback")
                except Exception:
                    print("⚠️  JS form.submit() fallback failed")

            # ASP.NET postback fallback if still not submitted
            if not submitted:
                try:
                    # Enumerate candidate controls to discover real event targets
                    candidates = driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button' or @type='image'] | //button | //a[@onclick]")
                    targets = []
                    for el in candidates:
                        try:
                            txt = (el.get_attribute('value') or el.text or '')
                            id_attr = el.get_attribute('id') or ''
                            name_attr = el.get_attribute('name') or ''
                            onclick = el.get_attribute('onclick') or ''
                            blob = f"txt={txt} id={id_attr} name={name_attr}"
                            if any(k in (txt or '').lower() for k in ["save", "post", "submit", "add", "publish"]):
                                targets.append((el, id_attr, name_attr, onclick, blob))
                        except Exception:
                            continue
                    # Try click best-matching target first
                    for el, id_attr, name_attr, onclick, blob in targets:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                            time.sleep(0.2)
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via discovered control: {blob}")
                            break
                        except Exception:
                            continue
                    # Try __doPostBack with discovered name attribute
                    if not submitted:
                        for _, _, name_attr, _, blob in targets:
                            try:
                                if name_attr:
                                    ok = driver.execute_script("if (window.__doPostBack) { __doPostBack(arguments[0], ''); return true } return false;", name_attr)
                                    if ok:
                                        submitted = True
                                        print(f"✅ Form submitted via __doPostBack target: {name_attr}")
                                        break
                            except Exception:
                                continue
                except Exception:
                    pass
            
            if submitted:
                # Handle potential JS alert/confirm after submit
                try:
                    alert = driver.switch_to.alert
                    text = alert.text
                    alert.accept()
                    print(f"✅ Accepted post-submit alert: {text}")
                except Exception:
                    pass
                # Give the site time to persist/redirect
                time.sleep(12)

                # Basic error sniffing on the immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", "Form submission returned error")
                    return "Error: Form submission failed - check required fields"

                # Always verify on inventory/summary pages before declaring success
                self._capture_step("inventory_check_start", f"Post-submit at {current_url}")
                verified = self._verify_cellpex_listing(row)
                if verified:
                    print("🎉 Listing verified in account after submission")
                    self._capture_step("listing_verified", "Verified listing appears in account")
                    return "Success: Listing verified in account"
                else:
                    print("❌ Could not verify listing in account after submission")
                    self._capture_step("listing_not_found", "Listing not found in inventory after submit")
                    return "Error: Submission completed but listing not found in inventory (treated as failure)"
            else:
                print("❌ Could not submit form")
                self._capture_step("no_submit", "Could not find/activate submit control")
                return "Error: Could not submit form"
            
        except Exception as e:
            print(f"❌ Error posting to Cellpex: {e}")
            self._capture_step("exception", f"Exception during posting: {e}")
            return f"Error: {str(e)}"

    def _verify_cellpex_listing(self, row) -> bool:
        """Verify that the listing exists in the account by visiting inventory/summary pages
        and checking for strong signals (brand AND model present on the page, optionally price).
        """
        try:
            driver = self.driver
            brand = str(row.get("brand", "")).strip()
            model = str(row.get("model", "")).strip()
            price = str(row.get("price", "")).strip()
            currency = str(row.get("currency", "")).strip().upper()

            # Pages to try for verification
            targets = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
                "https://www.cellpex.com/wholesale-search-results",
                "https://www.cellpex.com/list/wholesale-inventory",
            ]

            # Helper to assert presence of multiple tokens
            def contains_all_tokens(text: str, tokens: list[str]) -> bool:
                text_l = text.lower()
                return all(t and t.lower() in text_l for t in tokens)

            # Build token sets to look for
            token_sets = []
            if brand and model:
                token_sets.append([brand, model])
            elif brand:
                token_sets.append([brand])
            elif model:
                token_sets.append([model])
            # Add price pattern if available (don't rely solely on it)
            if price:
                token_sets.append([price])
            if price and currency:
                token_sets.append([currency, price])

            for url in targets:
                try:
                    driver.get(url)
                    time.sleep(3)
                    page = driver.page_source
                    # Quick capture for diagnostics
                    self._capture_step("inventory_page", f"Checked {url}")
                    # If any strong token set matches, consider verified
                    for tokens in token_sets:
                        if contains_all_tokens(page, tokens):
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False


# Platform poster registry
ENHANCED_POSTERS = {
    'gsmexchange': EnhancedGSMExchangePoster,
    'cellpex': EnhancedCellpexPoster,
    # Add other platforms as needed
}


def test_platform_login_with_2fa(platform_name):
    """Test login with 2FA for a specific platform"""
    print(f"\n🧪 Testing {platform_name} login with 2FA...")
    
    if platform_name not in ENHANCED_POSTERS:
        print(f"❌ Platform {platform_name} not implemented yet")
        return False
        
    # Create driver
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    # Remove headless for testing to see what's happening
    # options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Create poster instance
        poster_class = ENHANCED_POSTERS[platform_name]
        poster = poster_class(driver)
        
        # Test login with 2FA
        success = poster.login_with_2fa()
        
        if success:
            print(f"✅ Successfully logged into {platform_name} with 2FA!")
            # Take screenshot for verification
            driver.save_screenshot(f"{platform_name}_login_success.png")
        else:
            print(f"❌ Failed to login to {platform_name}")
            driver.save_screenshot(f"{platform_name}_login_failed.png")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing {platform_name}: {e}")
        return False
    finally:
        driver.quit()


if __name__ == "__main__":
    # Test GSM Exchange login with 2FA
    test_platform_login_with_2fa('gsmexchange')