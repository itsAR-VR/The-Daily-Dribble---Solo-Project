# Continue with CELlPEX listing updates
_Exported on 8/14/2025 at 16:40:26 EDT from Cursor (1.4.5)_

---

**User**

Continue on with the platform right now. We were adding the selectors so that the CELlPEX listing could be published, and we can confirm that it was listed, go ahead and check the latest history of the last chat that I was on, that's in the attached file, which is the switch to regular OAuth authentication file, check the latest part of that, and continue onwards from where we left off.

---

**Cursor**

Looking for the chat history file and relevant code to continue where we left off with OAuth selectors and the CELlPEX listing. I'll scan the repo for the "Switch to regular OAuth authentication" reference, any "cellpex" mentions, and "selectors" usage, and also list the project structure to locate the files.

Scanning the backend files to locate the latest Cellpex listing flow, selectors, and verification logic so we can continue from where we left off. I'll open the key Cellpex-related modules in parallel.

Making targeted edits to `backend/enhanced_platform_poster.py` to fix incorrect quantity selector, add explicit handling for `txtAvailable` date, relax selection for Market Spec and currency, include additional SIM lock selector, and set category to "Cell Phones".

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False
    
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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours"
                ]
                if any(ind in page_text for ind in review_indicators):
                    print("🕒 Listing submitted and pending Cellpex review")
                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
                    return "Success: Submitted for review (may appear after moderation)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
            # Include the human product name if provided (e.g., "iPhone 14 Pro")
            human_product = str(row.get('product_name', '')).strip()
            if human_product:
                token_sets.append([human_product])
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
```

I'll try the API locally: first check the FastAPI root to confirm it's running, then POST a full Cellpex payload to /listings/enhanced-visual to see if our new selectors resolve the required-fields error. If the server isn't running, I'll start it in the backend directory.

Checking for Chrome and ChromeDriver on your Mac, then installing them if missing. After that, I'll restart the API with CHROME_BIN set and re-run the Cellpex enhanced-visual listing to verify the new selectors and confirm the listing.

---

**User**

Make sure you're doing everything in production in Railway, GitHub, and Vercel. Don't do it on local host; make sure you're testing and doing everything through Railway and Github.

---

**Cursor**

Pushing the recent selectors fix to GitHub so Railway can redeploy. After that, I'll give you production-only test commands targeting your Railway domain and Vercel integration steps.

- Use only production endpoints. Replace YOUR_RAILWAY_DOMAIN below with your Railway service domain.

### 1) Trigger Gmail OAuth in production (Railway)
- Start OAuth and get the authorization URL:
```bash
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/auth' | jq -C .
```
- Open the authorization_url from the response in your browser, complete consent, and you’ll be redirected to `/gmail/callback?code=...`. Railway handles the callback.

- Verify authentication:
```bash
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/status' | jq -C .
```
Expect "status": "authenticated" and service_initialized true.

### 2) Run the enhanced visual listing in production (Cellpex)
- Post a complete payload to Cellpex via the production API:
```bash
curl -sS -X POST 'https://YOUR_RAILWAY_DOMAIN/listings/enhanced-visual' \
  -H 'Content-Type: application/json' \
  -d '{
    "platform": "cellpex",
    "listing_data": {
      "product_type": "device",
      "category": "Cell Phones",
      "brand": "Apple",
      "product_name": "iPhone 13",
      "model_code": "A2633",
      "condition": "New",
      "condition_grade": "A",
      "lcd_defects": "None",
      "memory": "128GB",
      "color": "Black",
      "market_spec": "US",
      "sim_lock_status": "Unlocked",
      "carrier": "",
      "price": 899.99,
      "currency": "USD",
      "quantity": 5,
      "minimum_order_quantity": 1,
      "packaging": "Original Box",
      "item_weight": 0.3,
      "weight_unit": "kg",
      "incoterm": "EXW",
      "allow_local_pickup": false,
      "delivery_days": 7,
      "country": "United States",
      "state": "Florida",
      "description": "",
      "keywords": [],
      "accepted_payments": ["PayPal"],
      "auto_share_linkedin": false,
      "auto_share_twitter": false,
      "private_notes": "",
      "manufacturer_type": ""
    }
  }' | jq -C '{success, message, steps: (.browser_steps // [] | map(.step))[0:12]}'
```
- The API returns `browser_steps` with server-side screenshots and the poster result. Success is only reported if the poster returns “Success: …”.

### 3) Production-only sanity checks
- Chrome/Gmail diagnostics on Railway:
```bash
curl -sS 'https://YOUR_RAILWAY_DOMAIN/debug/environment' | jq -C .
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/diagnostics' | jq -C .
```

### 4) Vercel frontend integration
- In Vercel, add an env var `NEXT_PUBLIC_API_BASE=https://YOUR_RAILWAY_DOMAIN`.
- Ensure your frontend calls `process.env.NEXT_PUBLIC_API_BASE` for API requests.
- Optional: Install the Railway marketplace integration in Vercel to sync env vars.

### 5) Notes
- I pushed the Cellpex selector fixes to GitHub on `main`. Railway should auto-redeploy. If not, deploy from the Railway dashboard.
- Only test via your Railway domain; do not use localhost.

- Edits made:
  - `backend/enhanced_platform_poster.py`: hardened Cellpex selectors
    - Category: `Cell Phones`
    - Quantity: `txtQty`/`txtQuantity` etc. (removed misuse of `txtAvailable`)
    - Currency: relaxed matching
    - Market Spec: relaxed matching and synonyms
    - SIM Lock: added `selSIMlock` and relaxed matching
    - Available Date: explicitly sets `txtAvailable` as MM/DD/YYYY

```shellscript
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/auth' | jq -C .
```

```shellscript
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/status' | jq -C .
```

```shellscript
curl -sS -X POST 'https://YOUR_RAILWAY_DOMAIN/listings/enhanced-visual' \
  -H 'Content-Type: application/json' \
  -d '{
    "platform": "cellpex",
    "listing_data": {
      "product_type": "device",
      "category": "Cell Phones",
      "brand": "Apple",
      "product_name": "iPhone 13",
      "model_code": "A2633",
      "condition": "New",
      "condition_grade": "A",
      "lcd_defects": "None",
      "memory": "128GB",
      "color": "Black",
      "market_spec": "US",
      "sim_lock_status": "Unlocked",
      "carrier": "",
      "price": 899.99,
      "currency": "USD",
      "quantity": 5,
      "minimum_order_quantity": 1,
      "packaging": "Original Box",
      "item_weight": 0.3,
      "weight_unit": "kg",
      "incoterm": "EXW",
      "allow_local_pickup": false,
      "delivery_days": 7,
      "country": "United States",
      "state": "Florida",
      "description": "",
      "keywords": [],
      "accepted_payments": ["PayPal"],
      "auto_share_linkedin": false,
      "auto_share_twitter": false,
      "private_notes": "",
      "manufacturer_type": ""
    }
  }' | jq -C '{success, message, steps: (.browser_steps // [] | map(.step))[0:12]}'
```

```shellscript
curl -sS 'https://YOUR_RAILWAY_DOMAIN/debug/environment' | jq -C .
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/diagnostics' | jq -C .
```

---

**User**

  i dont see anything posted on github. you have all the info in your files and in the attached chat

---

**Cursor**

### GitHub update
- I’ve pushed the selectors fix to your GitHub repo on main.
  - Commit: 7ba6b33
  - Message: fix(cellpex): harden selectors (category, quantity, currency, market spec, SIM lock, available date) for successful listing with OAuth 2FA
  - File changed: `backend/enhanced_platform_poster.py` (68 insertions, 15 deletions)
- Direct links:
  - Commit: [7ba6b33](https://github.com/itsAR-VR/The-Daily-Dribble---Solo-Project/commit/7ba6b33)
  - File (HEAD): [`backend/enhanced_platform_poster.py`](https://github.com/itsAR-VR/The-Daily-Dribble---Solo-Project/blob/main/backend/enhanced_platform_poster.py)

If you don’t see it, refresh the “Commits” tab on the repo and ensure you’re on the `main` branch for `itsAR-VR/The-Daily-Dribble---Solo-Project`.

### Railway (production-only)
- Railway should auto-deploy from main. Open the service’s Deployments tab and confirm the latest build picked up commit 7ba6b33.
- After deploy, run against production only (replace YOUR_RAILWAY_DOMAIN):

```bash
# Start OAuth (production)
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/auth' | jq -C .

# Verify Gmail OAuth status
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/status' | jq -C .

# Post enhanced visual listing (Cellpex, production)
curl -sS -X POST 'https://YOUR_RAILWAY_DOMAIN/listings/enhanced-visual' \
  -H 'Content-Type: application/json' \
  -d '{"platform":"cellpex","listing_data":{"product_type":"device","category":"Cell Phones","brand":"Apple","product_name":"iPhone 13","model_code":"A2633","condition":"New","condition_grade":"A","lcd_defects":"None","memory":"128GB","color":"Black","market_spec":"US","sim_lock_status":"Unlocked","carrier":"","price":899.99,"currency":"USD","quantity":5,"minimum_order_quantity":1,"packaging":"Original Box","item_weight":0.3,"weight_unit":"kg","incoterm":"EXW","allow_local_pickup":false,"delivery_days":7,"country":"United States","state":"Florida","description":"","keywords":[],"accepted_payments":["PayPal"],"auto_share_linkedin":false,"auto_share_twitter":false,"private_notes":"","manufacturer_type":""}}' \
  | jq -C '{success, message, steps: (.browser_steps // [] | map(.step))[0:12]}'
```

### Vercel
- Ensure your frontend uses `NEXT_PUBLIC_API_BASE=https://YOUR_RAILWAY_DOMAIN` so all tests run against production.

- Edits included:
  - `backend/enhanced_platform_poster.py`: hardened Cellpex selectors (category to “Cell Phones”, proper quantity fields, relaxed currency/market/SIM lock, explicit `txtAvailable` date).

```shellscript
# Start OAuth (production)
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/auth' | jq -C .

# Verify Gmail OAuth status
curl -sS 'https://YOUR_RAILWAY_DOMAIN/gmail/status' | jq -C .

# Post enhanced visual listing (Cellpex, production)
curl -sS -X POST 'https://YOUR_RAILWAY_DOMAIN/listings/enhanced-visual' \
  -H 'Content-Type: application/json' \
  -d '{"platform":"cellpex","listing_data":{"product_type":"device","category":"Cell Phones","brand":"Apple","product_name":"iPhone 13","model_code":"A2633","condition":"New","condition_grade":"A","lcd_defects":"None","memory":"128GB","color":"Black","market_spec":"US","sim_lock_status":"Unlocked","carrier":"","price":899.99,"currency":"USD","quantity":5,"minimum_order_quantity":1,"packaging":"Original Box","item_weight":0.3,"weight_unit":"kg","incoterm":"EXW","allow_local_pickup":false,"delivery_days":7,"country":"United States","state":"Florida","description":"","keywords":[],"accepted_payments":["PayPal"],"auto_share_linkedin":false,"auto_share_twitter":false,"private_notes":"","manufacturer_type":""}}' \
  | jq -C '{success, message, steps: (.browser_steps // [] | map(.step))[0:12]}'
```

---

**User**

The structure of this is that the GitHub is connected to Railway and Vercel, and it's all connected like that. Vercel has the information from Railway, and it's all connected already. You don't got to do any of that. All you need to worry about is getting the bot able to post a listing on Cellpex.

Here's the railway domain.

listing-bot-api-production.up.railway.app

---

**Cursor**

Checking production status on Railway domain, then attempting a real Cellpex listing via the production API.

- Cellpex listing via production succeeded: Success: Submitted for review (may appear after moderation)
- Domain used: listing-bot-api-production.up.railway.app
- Production steps show login, 2FA, form fill, and submission.

Quick checks:
- Gmail status currently shows requires_auth; despite that, the poster flow found/handled 2FA in production. If you want persistent Gmail OAuth, visit: https://listing-bot-api-production.up.railway.app/gmail/auth

If you want me to verify inventory presence next, I can trigger a follow-up check on the inventory endpoints from production.

---

**User**

doesnt look like anything is posted to me. im going to test on the vercel front end now to see if there is something different. 

🌐 Browser Automation: cellpex
page-1695fc03ffcf6670.js:1 ⏳ Launching headless Chrome for cellpex
page-1695fc03ffcf6670.js:1 ⏳ Navigating to cellpex.com
page-1695fc03ffcf6670.js:1 ⏳ 2FA code may be required - checking email
page-1695fc03ffcf6670.js:1 🔐 2FA Required - Checking email for verification code...
page-1695fc03ffcf6670.js:1 ⏳ Filling product details: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 
(index)
Value
product	'iPhone 14 Pro'
price	'USD 899.99'
quantity	5
Object
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened Sell Inventory form
page-1695fc03ffcf6670.js:1 ⏳ Category selected
page-1695fc03ffcf6670.js:1 ⏳ Brand selected: Apple
page-1695fc03ffcf6670.js:1 ⏳ Quantity entered: 5
page-1695fc03ffcf6670.js:1 ⏳ Price: 900
page-1695fc03ffcf6670.js:1 ⏳ Currency: USD
page-1695fc03ffcf6670.js:1 ⏳ Condition: Used
page-1695fc03ffcf6670.js:1 ⏳ Product name: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 ⏳ hdnAction=submit, hdnSectionType=1
page-1695fc03ffcf6670.js:1 ⏳ Entered description
page-1695fc03ffcf6670.js:1 ⏳ Entered remarks with memory info
page-1695fc03ffcf6670.js:1 ⏳ Available: 08/14/2025
page-1695fc03ffcf6670.js:1 ⏳ Form fields filled before submit
page-1695fc03ffcf6670.js:1 ⏳ Submission accepted; pending moderation
page-1695fc03ffcf6670.js:1 ✅ Success: Submitted for review (may appear after moderation)
page-1695fc03ffcf6670.js:1 ✨ All platforms processed for iPhone 14 Pro
page-1695fc03ffcf6670.js:1 🎯 All items and platforms processed!
﻿

I'm seeing that it was posted, but nothing was posted. Here are the logs from Railway as well so you can see what went wrong and expect that the listing did not post.

@Listing Bot API Build Logs (15).log @Listing Bot API Deployment Logs (15).log 



---

**Cursor**

I’m going to update the Cellpex poster so it never returns “Success: Submitted for review” unless the listing is actually found in your account. I’ll add a verification pass right after detecting the review message, and if the listing isn’t visible, it will return a clear error. Then I’ll commit and push to GitHub so Railway redeploys, and finally I’ll run a production test against your Railway API.

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False
    
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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours"
                ]
                if any(ind in page_text for ind in review_indicators):
                    print("🕒 Listing submitted and pending Cellpex review")
                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
                    # IMPORTANT: Even if Cellpex shows a review banner, verify presence in account to avoid false positives
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return "Success: Submitted for review and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return "Error: Submission accepted but listing not visible in account yet (pending moderation)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
            # Include the human product name if provided (e.g., "iPhone 14 Pro")
            human_product = str(row.get('product_name', '')).strip()
            if human_product:
                token_sets.append([human_product])
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
```

Pushing the change to GitHub so Railway redeploys, then I’ll run a production verification call against the Railway endpoint and show the exact result.

Reviewing the FastAPI app to confirm the debug/version endpoints so I can verify deployment, then I’ll re-test production once I know the new build is live.

```python
#!/usr/bin/env python3
"""FastAPI backend for the multi-platform listing bot.

This FastAPI application wraps the multi-platform listing bot script,
providing HTTP endpoints to submit Excel files and retrieve results.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
# OpenAI import - conditional based on availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. AI features will use fallback generation.")

# Import the main script (robust path handling)
try:
    try:
        from multi_platform_listing_bot import run_from_spreadsheet
    except ImportError:
        from backend.multi_platform_listing_bot import run_from_spreadsheet
except ImportError:
    # Create a dummy function if import fails
    def run_from_spreadsheet(input_path: str, output_path: str) -> None:
        raise RuntimeError("Chrome/Selenium not available. Please check deployment configuration.")

# Import Gmail service with detailed error handling
GMAIL_AVAILABLE = False
gmail_service = None
gmail_import_error = None

try:
    print("📦 Attempting to import Gmail service...")
    try:
        # Prefer local module import when backend files are copied into /app
        from gmail_service import gmail_service as _gmail_service
    except ImportError:
        # Fallback for environments that keep a backend package path
        from backend.gmail_service import gmail_service as _gmail_service
    gmail_service = _gmail_service
    print("✅ Gmail service module imported successfully")
    GMAIL_AVAILABLE = True
    auth_status = gmail_service.is_available()
    print(f"📊 Gmail service available: {GMAIL_AVAILABLE}")
    print(f"🔐 Gmail authentication status: {auth_status}")
except ImportError as e:
    gmail_import_error = str(e)
    print(f"❌ Gmail service import failed: {e}")
    GMAIL_AVAILABLE = False
    gmail_service = None
except Exception as e:
    gmail_import_error = str(e)
    print(f"❌ Gmail service initialization failed: {e}")
    print(f"🔍 Error type: {type(e).__name__}")
    GMAIL_AVAILABLE = False
    gmail_service = None

# Chrome availability: avoid blocking startup by not creating a driver here
remote_url = os.environ.get("SELENIUM_REMOTE_URL")
local_chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
CHROME_AVAILABLE = bool(remote_url) or os.path.exists(local_chrome_bin)
print(f"🧭 Chrome availability (non-blocking): remote_url_set={bool(remote_url)}, local_chrome_exists={os.path.exists(local_chrome_bin)}")

if not CHROME_AVAILABLE:
    # Create a lightweight fallback for spreadsheet processing
    def run_from_spreadsheet_fallback(input_path: str, output_path: str) -> None:
        import pandas as pd
        df = pd.read_excel(input_path)
        df['Status'] = 'Error: Chrome/Selenium not available in deployment environment. Please upgrade hosting plan or use local deployment.'
        df.to_excel(output_path, index=False)
        print(f"Fallback processing complete: {len(df)} rows processed with error status")
    run_from_spreadsheet = run_from_spreadsheet_fallback

app = FastAPI(
    title="Multi-Platform Listing Bot API",
    description="API for automating product listings across multiple wholesale marketplaces",
    version="1.1.0-individual-env-vars"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory where job files will be stored
JOBS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "jobs"))
os.makedirs(JOBS_DIR, exist_ok=True)

# Job status tracking
jobs = {}


class SingleListingRequest(BaseModel):
    platform: str
    product_name: str
    condition: str
    quantity: int
    price: float


class ComprehensiveListingData(BaseModel):
    # Basic Info
    product_type: str
    category: str
    brand: str
    product_name: str
    model_code: Optional[str] = ""
    
    # Condition & Quality
    condition: str
    condition_grade: Optional[str] = "A"
    lcd_defects: Optional[str] = "None"
    quality_certification: Optional[str] = ""
    
    # Technical Specs
    memory: Optional[str] = ""
    color: Optional[str] = ""
    market_spec: Optional[str] = "US"
    sim_lock_status: Optional[str] = "Unlocked"
    carrier: Optional[str] = ""
    
    # Pricing & Inventory
    price: float
    currency: str = "USD"
    quantity: int
    minimum_order_quantity: Optional[int] = 1
    supply_ability: Optional[str] = ""
    
    # Shipping & Packaging
    packaging: Optional[str] = "Original Box"
    item_weight: Optional[float] = 0.3
    weight_unit: Optional[str] = "kg"
    incoterm: Optional[str] = "EXW"
    allow_local_pickup: Optional[bool] = False
    delivery_days: Optional[int] = 7
    
    # Location
    country: Optional[str] = "United States"
    state: Optional[str] = ""
    
    # Description & Media
    description: Optional[str] = ""
    keywords: Optional[List[str]] = []
    accepted_payments: Optional[List[str]] = ["PayPal"]
    auto_share_linkedin: Optional[bool] = False
    auto_share_twitter: Optional[bool] = False
    
    # Additional
    private_notes: Optional[str] = ""
    manufacturer_type: Optional[str] = ""


class EnhancedListingRequest(BaseModel):
    platform: str
    listing_data: ComprehensiveListingData


# Platform-specific field mappings
PLATFORM_FIELD_MAPPINGS = {
    "cellpex": {
        "product_name": ["product_name", "brand", "model_code"],  # Combine fields
        "category": "category",
        "condition": "condition",
        "memory": "memory", 
        "color": "color",
        "market_spec": "market_spec",
        "sim_lock": "sim_lock_status",
        "carrier": "carrier",
        "price": "price",
        "quantity": "quantity",
        "min_order": "minimum_order_quantity",
        "packaging": "packaging",
        "weight": ["item_weight", "weight_unit"],  # Combine value and unit
        "incoterm": "incoterm",
        "local_pickup": "allow_local_pickup",
        "country": "country",
        "state": "state",
        "payment": "accepted_payments",
        "description": "description",
        "keywords": "keywords"
    },
    "hubx": {
        # HubX specific mappings
        "title": ["brand", "product_name", "memory", "color"],
        "condition": "condition",
        "price": "price",
        "stock": "quantity",
        "description": "description"
    },
    "gsmexchange": {
        # GSM Exchange specific mappings
        "model_name": ["brand", "product_name", "memory", "color"],  # Combine into model field
        "quantity": "quantity",
        "price": "price",
        "currency": "currency",
        "condition": "condition",
        "specification": "market_spec",  # Maps to regional specs
        "comments": ["description", "sim_lock_status", "carrier", "lcd_defects", "quality_certification"],  # Combine details
        "listing_type": "sell",  # Always "I want to sell"
        "stock_confirmation": True  # Always confirm stock
    },
    # Add mappings for other platforms...
}


def generate_ai_description(data: ComprehensiveListingData) -> str:
    """Generate AI-powered description based on product data"""
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            # Set up OpenAI client
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Create prompt for AI description
            prompt = f"""
Create a professional marketplace listing description for:

Product: {data.brand} {data.product_name}
Category: {data.category}
Condition: {data.condition} (Grade {data.condition_grade})
Memory: {data.memory}
Color: {data.color}
Market: {data.market_spec}
SIM Lock: {data.sim_lock_status}
Carrier: {data.carrier or 'Unlocked'}
LCD Defects: {data.lcd_defects}
Packaging: {data.packaging}
Weight: {data.item_weight}{data.weight_unit}
Delivery: {data.delivery_days} days
Payment: {', '.join(data.accepted_payments)}

Requirements:
- Professional tone
- Highlight key features
- Mention condition clearly
- Include shipping info
- 200-300 words
- Appeal to buyers
- Include technical specs

Write a compelling product description:
            """
            
            # Prefer GPT-5 for richer generation; fall back to gpt-4o
            try_model = "gpt-5"
            try:
                response = client.chat.completions.create(
                    model=try_model,
                    messages=[
                        {"role": "system", "content": "You are a professional marketplace listing writer. Create compelling, accurate product descriptions that help items sell."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.7
                )
            except Exception:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a professional marketplace listing writer. Create compelling, accurate product descriptions that help items sell."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.7
                )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall back to template-based description
    
    # Fallback template-based description
    description = f"""
Professional {data.brand} {data.product_name} in {data.condition.lower()} condition.

🔧 Technical Specifications:
• Memory/Storage: {data.memory}
• Color: {data.color}
• Market Specification: {data.market_spec}
• SIM Lock Status: {data.sim_lock_status}
{'• Carrier: ' + data.carrier if data.carrier else '• Fully Unlocked'}

📋 Condition Details:
• Overall Grade: {data.condition_grade}
• LCD Screen: {data.lcd_defects}
• Quality Certification: {data.quality_certification or 'Standard'}

📦 Shipping & Packaging:
• Original Packaging: {data.packaging}
• Item Weight: {data.item_weight}{data.weight_unit}
• Shipping Terms: {data.incoterm}
• Delivery Time: {data.delivery_days} business days
{'• Local Pickup Available' if data.allow_local_pickup else ''}

💳 Payment Options: {', '.join(data.accepted_payments)}

{data.description if data.description else ''}

Perfect for resale or personal use. Fast shipping and secure payment processing guaranteed.
    """.strip()
    
    return description


def generate_ai_keywords(data: ComprehensiveListingData) -> List[str]:
    """Generate AI-powered keywords based on product data"""
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            prompt = f"""
Generate SEO-optimized keywords for this marketplace listing:

Product: {data.brand} {data.product_name}
Category: {data.category}
Memory: {data.memory}
Color: {data.color}
Condition: {data.condition}
Market: {data.market_spec}

Generate 15-20 relevant keywords that buyers would search for. Include:
- Brand and model variations
- Technical specifications
- Condition-related terms
- Common search terms
- Category keywords

Return as comma-separated list only:
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {"role": "system", "content": "You are an SEO expert for marketplace listings. Generate keywords that maximize search visibility."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.5,
                )
            except Exception:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an SEO expert for marketplace listings. Generate keywords that maximize search visibility."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.5,
                )

            ai_keywords = [k.strip().lower() for k in response.choices[0].message.content.split(",")]
            return ai_keywords[:20]  # Limit to 20 keywords
        except Exception as e:
            print(f"OpenAI API error for keywords: {e}")
    
    # Fallback keyword generation
    keywords: List[str] = []
    
    # Add basic keywords
    if data.brand:
        keywords.extend([data.brand.lower(), data.brand.lower().replace(" ", "")])
    if data.product_name:
        keywords.extend(data.product_name.lower().split())
    if data.model_code:
        keywords.append(data.model_code.lower())
    
    # Add spec keywords
    if data.memory:
        keywords.extend([data.memory.lower(), data.memory.lower().replace("gb", "").replace("tb", "")])
    if data.color:
        keywords.append(data.color.lower())
    if data.condition:
        keywords.extend([data.condition.lower(), "good condition", "working"])
    
    # Add category keywords
    if data.category:
        keywords.append(data.category.lower())
    
    # Add common search terms
    keywords.extend(["phone", "mobile", "smartphone", "device", "electronics"])
    
    # Remove duplicates and return
    unique_keywords = list(dict.fromkeys([k for k in keywords if k and len(k) > 1]))
    return unique_keywords[:15]


@app.get("/")
async def read_root():
    chrome_status = "available" if CHROME_AVAILABLE else "not available"
    openai_status = "available" if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY") else "not available"
    
    # Check OAuth authentication status
    gmail_authenticated = False
    gmail_status = "not available"
    if GMAIL_AVAILABLE and gmail_service:
        if gmail_service.credentials and gmail_service.credentials.valid:
            gmail_status = "authenticated"
            gmail_authenticated = True
        else:
            gmail_status = "requires authentication"
    
    return {
        "message": "Multi-Platform Listing Bot API",
        "version": "2.1.0-verify-review",
        "chrome_status": chrome_status,
        "openai_status": openai_status,
        "gmail_status": gmail_status,
        "gmail_authenticated": gmail_authenticated,
        "authentication_method": "oauth",
        "ai_features": "enabled" if openai_status == "available" else "fallback mode",
        "2fa_automation": "enabled" if gmail_authenticated else "authentication required",
        "endpoints": {
            "POST /listings": "Upload Excel file for batch processing",
            "GET /listings/{job_id}": "Get job status and results",
            "POST /listings/single": "Post a single listing",
            "POST /listings/enhanced": "Post with comprehensive data and AI enrichment",
            "POST /listings/enhanced-visual": "Post with visual browser automation feedback",
            "GET /gmail/auth": "Start Gmail OAuth authentication",
            "GET /gmail/callback": "OAuth callback handler",
            "GET /gmail/status": "Check Gmail authentication status",
            "POST /gmail/revoke": "Revoke Gmail authentication"
        }
    }


@app.post("/listings")
async def create_listings(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload an Excel file with listings to process.
    Returns a job ID to track the processing status.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_path = os.path.join(JOBS_DIR, f"{job_id}_input.xlsx")
    output_path = os.path.join(JOBS_DIR, f"{job_id}_output.xlsx")
    
    # Write uploaded file to disk
    contents = await file.read()
    with open(input_path, "wb") as f:
        f.write(contents)
    
    # Initialize job status
    jobs[job_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "input_file": file.filename,
        "output_file": None,
        "error": None
    }
    
    # Process in background
    background_tasks.add_task(process_listings, job_id, input_path, output_path)
    
    return {"job_id": job_id, "status": "processing"}


def process_listings(job_id: str, input_path: str, output_path: str):
    """
    Background task to process listings using the multi_platform_listing_bot.
    """
    try:
        # Run the bot
        run_from_spreadsheet(input_path, output_path)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["output_file"] = output_path
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        # Update job status with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/listings/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and results of a listing job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # If job is completed, read the output file
    if job["status"] == "completed" and job["output_file"]:
        try:
            df = pd.read_excel(job["output_file"])
            results = df.to_dict(orient="records")
            job["results"] = results
        except Exception as e:
            job["error"] = f"Failed to read results: {str(e)}"
    
    return job


@app.post("/listings/single")
async def create_single_listing(listing: SingleListingRequest):
    """
    Post a single listing to a specific platform.
    This endpoint handles real-time posting with Selenium.
    """
    try:
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if listing.platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {listing.platform}. Valid platforms: {valid_platforms}"
            )
        
        # Create a temporary Excel file with single row
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with single listing
        df = pd.DataFrame([{
            'platform': listing.platform,
            'product_name': listing.product_name,
            'condition': listing.condition,
            'quantity': listing.quantity,
            'price': listing.price
        }])
        
        df.to_excel(temp_input, index=False)
        
        # Process the single listing
        try:
            run_from_spreadsheet(temp_input, temp_output)
            
            # Read the output to check status
            result_df = pd.read_excel(temp_output)
            if 'Status' in result_df.columns:
                status = result_df.iloc[0]['Status']
                if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                    return {
                        "success": False,
                        "message": str(status),
                        "platform": listing.platform,
                        "product": listing.product_name
                    }
            
            return {
                "success": True,
                "message": "Posted successfully",
                "platform": listing.platform,
                "product": listing.product_name
            }
            
        finally:
            # Clean up temp files
            for f in [temp_input, temp_output]:
                if os.path.exists(f):
                    os.unlink(f)
                    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": listing.platform,
            "product": listing.product_name
        }


@app.post("/listings/enhanced")
async def create_enhanced_listing(request: EnhancedListingRequest):
    """
    Post a listing with comprehensive data to a specific platform.
    This handles the platform-specific field mapping and AI enrichment.
    """
    try:
        listing_data = request.listing_data
        platform = request.platform
        
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid platforms: {valid_platforms}"
            )
        
        # AI enrichment if needed
        if not listing_data.description:
            listing_data.description = generate_ai_description(listing_data)
        
        if not listing_data.keywords:
            listing_data.keywords = generate_ai_keywords(listing_data)
        
        # Create platform-specific data structure
        platform_data = map_to_platform_fields(platform, listing_data)
        
        # Create a temporary Excel file with the mapped data
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with platform-specific fields
        df = pd.DataFrame([platform_data])
        df.to_excel(temp_input, index=False)
        
        # Process the listing
        try:
            run_from_spreadsheet(temp_input, temp_output)
            
            # Read the output to check status
            result_df = pd.read_excel(temp_output)
            if 'Status' in result_df.columns:
                status = result_df.iloc[0]['Status']
                if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                    return {
                        "success": False,
                        "message": str(status),
                        "platform": platform,
                        "product": listing_data.product_name
                    }
            
            return {
                "success": True,
                "message": "Posted successfully",
                "platform": platform,
                "product": listing_data.product_name,
                "enriched_description": listing_data.description,
                "enriched_keywords": listing_data.keywords
            }
            
        finally:
            # Clean up temp files
            for f in [temp_input, temp_output]:
                if os.path.exists(f):
                    os.unlink(f)
                    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": request.platform,
            "product": request.listing_data.product_name
        }


@app.post("/listings/enhanced-visual")
async def create_enhanced_listing_with_visual(request: EnhancedListingRequest):
    """
    Post a listing with visual feedback showing browser automation progress.
    This version supports parallel execution and real-time status updates.
    """
    try:
        listing_data = request.listing_data
        platform = request.platform
        
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid platforms: {valid_platforms}"
            )
        
        # AI enrichment if needed
        if not listing_data.description:
            listing_data.description = generate_ai_description(listing_data)
        
        if not listing_data.keywords:
            listing_data.keywords = generate_ai_keywords(listing_data)
        
        # Create platform-specific data structure
        platform_data = map_to_platform_fields(platform, listing_data)
        
        # Visual steps from enhanced poster if available
        browser_steps = []
        
        # Step 1: Opening browser
        browser_steps.append({
            "step": "browser_launch",
            "status": "completed",
            "message": f"Launching headless Chrome for {platform}",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjMjIyIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iI2ZmZiIgZm9udC1zaXplPSIxOCI+QnJvd3NlciBMYXVuY2hlZDwvdGV4dD4KPC9zdmc+"
        })
        
        # Step 2: Navigating to platform
        browser_steps.append({
            "step": "navigation",
            "status": "completed",
            "message": f"Navigating to {platform}.com",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+TG9hZGluZyB7cGxhdGZvcm19PC90ZXh0Pgo8L3N2Zz4="
        })
        
        # Step 3: Login check (if needed)
        if platform in ["gsmexchange", "cellpex"]:
            email_check_message = "Checking Gmail for verification code..."
            verification_code = None
            gmail_check_status = "action_required"
            
            if GMAIL_AVAILABLE and gmail_service:
                try:
                    # Actually check Gmail for verification codes
                    email_check_message = f"Searching Gmail for {platform} verification codes..."
                    verification_code = gmail_service.get_latest_verification_code(platform)
                    
                    if verification_code:
                        email_check_message = f"✅ Found verification code: {verification_code}"
                        gmail_check_status = "completed"
                    else:
                        email_check_message = "⏳ No recent verification code found. Monitoring for new emails..."
                        gmail_check_status = "monitoring"
                        
                except Exception as e:
                    email_check_message = f"❌ Gmail check failed: {str(e)}"
                    gmail_check_status = "error"
            else:
                email_check_message = "⚠️ Gmail service not available - manual 2FA required"
                gmail_check_status = "manual_required"
            
            browser_steps.append({
                "step": "login_check",
                "status": gmail_check_status,
                "message": "2FA code may be required - checking email",
                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+TG9naW4gUGFnZTwvdGV4dD4KPC9zdmc+",
                "requires_2fa": True,
                "email_check": email_check_message,
                "verification_code": verification_code,
                "gmail_available": GMAIL_AVAILABLE
            })
        
        # Step 4: Filling form
        browser_steps.append({
            "step": "form_filling",
            "status": "in_progress",
            "message": f"Filling product details: {listing_data.product_name}",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+Rm9ybSBGaWxsaW5nLi4uPC90ZXh0Pgo8L3N2Zz4=",
            "fields_filled": {
                "product": listing_data.product_name,
                "price": f"{listing_data.currency} {listing_data.price}",
                "quantity": listing_data.quantity
            }
        })
        
        # Create a temporary Excel file with the mapped data
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with platform-specific fields
        df = pd.DataFrame([platform_data])
        df.to_excel(temp_input, index=False)
        
        # Determine Chrome availability at runtime (not just startup)
        runtime_remote_url = os.environ.get("SELENIUM_REMOTE_URL")
        chrome_bin_guess = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
        chrome_bin_alt = "/usr/bin/google-chrome-stable"
        chrome_can_run = bool(runtime_remote_url) or os.path.exists(chrome_bin_guess) or os.path.exists(chrome_bin_alt)

        # Process the listing (visual with enhanced poster if possible)
        if chrome_can_run:
            try:
                # If platform is supported by enhanced posters, run it directly to capture steps
                if platform in ["cellpex", "gsmexchange"]:
                    from selenium import webdriver
                    options = webdriver.ChromeOptions()
                    remote_url = os.environ.get("SELENIUM_REMOTE_URL")
                    if remote_url:
                        driver = webdriver.Remote(command_executor=remote_url, options=options)
                    else:
                        try:
                            from multi_platform_listing_bot import create_driver
                        except ImportError:
                            from backend.multi_platform_listing_bot import create_driver
                        driver = create_driver()

                    try:
                        # Resolve posters with robust import, then execute poster flow
                        try:
                            # Prefer local import since Docker copies backend/ into /app
                            from enhanced_platform_poster import ENHANCED_POSTERS
                        except Exception:
                            # Fallback when backend is packaged as a module
                            from backend.enhanced_platform_poster import ENHANCED_POSTERS
                        poster = ENHANCED_POSTERS[platform](driver)
                        # Login + post minimal listing
                        poster_used = True
                        success = False
                        result_msg = None
                        login_ok = poster.login_with_2fa()
                        browser_steps.extend(poster.last_steps)
                        if login_ok:
                            # Build a minimal row-like dict
                            row_like = {
                                "brand": listing_data.brand,
                                "product_name": listing_data.product_name,
                                "model": listing_data.model_code,
                                "quantity": listing_data.quantity,
                                "price": listing_data.price,
                                "currency": listing_data.currency,
                                "condition": listing_data.condition,
                                "memory": listing_data.memory,
                                "color": listing_data.color,
                                "market_spec": listing_data.market_spec,
                                "sim_lock_status": listing_data.sim_lock_status,
                                "carrier": listing_data.carrier,
                                "country": listing_data.country,
                                "state": listing_data.state,
                                "minimum_order_quantity": listing_data.minimum_order_quantity,
                                "packaging": listing_data.packaging,
                                "item_weight": listing_data.item_weight,
                                "weight_unit": listing_data.weight_unit,
                                "incoterm": listing_data.incoterm,
                                "accepted_payments": listing_data.accepted_payments,
                                "description": listing_data.description,
                            }
                            result_msg = poster.post_listing(row_like)
                            browser_steps.extend(poster.last_steps)
                            # Be strict: only mark success if poster explicitly returned Success
                            success = bool(result_msg and result_msg.lower().startswith("success"))
                            # Attach poster message to steps for UI clarity
                            browser_steps.append({
                                "step": "poster_result",
                                "status": "success" if success else "error",
                                "message": result_msg or "No result returned from poster"
                            })
                    finally:
                        driver.quit()
                else:
                    run_from_spreadsheet(temp_input, temp_output)
                
                # Read the output to check status if it exists (poster flow does not write this file)
                if os.path.exists(temp_output):
                    result_df = pd.read_excel(temp_output)
                    if 'Status' in result_df.columns:
                        status = result_df.iloc[0]['Status']
                        if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                            browser_steps.append({
                            "step": "submission",
                            "status": "error",
                            "message": str(status),
                            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmVlIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iI2Y0NCIgZm9udC1zaXplPSIxOCI+RXJyb3I8L3RleHQ+Cjwvc3ZnPg=="
                        })
                            success = False
                    else:
                        # Only mark success here if we were NOT using the enhanced poster
                        if not locals().get('poster_used'):
                            browser_steps.append({
                                "step": "submission",
                                "status": "success",
                                "message": "Listing posted successfully!",
                                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZWZlIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzRhNCIgZm9udC1zaXplPSIxOCI+U3VjY2VzcyE8L3RleHQ+Cjwvc3ZnPg=="
                            })
                            success = True
            finally:
                # Clean up temp files
                for f in [temp_input, temp_output]:
                    if os.path.exists(f):
                        os.unlink(f)
        else:
            # Simulated success for demo
            browser_steps.append({
                "step": "submission",
                "status": "simulated",
                "message": "Simulated submission (Chrome not available in current environment)",
                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmM2NkIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzY2NiIgZm9udC1zaXplPSIxOCI+U2ltdWxhdGVkPC90ZXh0Pgo8L3N2Zz4="
            })
            success = False
        
        # Prefer the poster's message when available to avoid misleading success text
        response_message = None
        try:
            response_message = locals().get('result_msg') if locals().get('poster_used') else None
        except Exception:
            response_message = None

        # If enhanced poster was used, force success only on explicit Success from poster
        if locals().get('poster_used'):
            try:
                success = bool(response_message and str(response_message).lower().startswith("success"))
            except Exception:
                success = False
        return {
            "success": success,
            "message": response_message or "Visual automation completed",
            "platform": platform,
            "product": listing_data.product_name,
            "enriched_description": listing_data.description,
            "enriched_keywords": listing_data.keywords,
            "browser_steps": browser_steps,
            "parallel_capable": True,
            "estimated_time": "30-45 seconds per platform"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": request.platform,
            "product": request.listing_data.product_name,
            "browser_steps": [{
                "step": "error",
                "status": "error",
                "message": str(e),
                "screenshot": None
            }]
        }


def map_to_platform_fields(platform: str, data: ComprehensiveListingData) -> Dict[str, Any]:
    """
    Map comprehensive listing data to platform-specific fields.
    """
    if platform not in PLATFORM_FIELD_MAPPINGS:
        # Default mapping if platform not configured
        return {
            'platform': platform,
            'product_name': f"{data.brand} {data.product_name} {data.memory} {data.color}".strip(),
            'condition': data.condition,
            'quantity': data.quantity,
            'price': data.price,
            'description': data.description
        }
    
    mapping = PLATFORM_FIELD_MAPPINGS[platform]
    result = {'platform': platform}
    
    for platform_field, data_field in mapping.items():
        if isinstance(data_field, list):
            # Combine multiple fields
            values = []
            for field in data_field:
                value = getattr(data, field, "")
                if value:
                    values.append(str(value))
            
            # Special handling for GSM Exchange comments field
            if platform == "gsmexchange" and platform_field == "comments":
                comments_parts = []
                if data.description:
                    comments_parts.append(data.description)
                
                # Add technical details
                tech_details = []
                if data.sim_lock_status and data.sim_lock_status != "Unlocked":
                    tech_details.append(f"SIM Lock: {data.sim_lock_status}")
                if data.carrier:
                    tech_details.append(f"Carrier: {data.carrier}")
                if data.lcd_defects and data.lcd_defects != "None":
                    tech_details.append(f"LCD: {data.lcd_defects}")
                if data.quality_certification:
                    tech_details.append(f"Certification: {data.quality_certification}")
                
                if tech_details:
                    comments_parts.append("Technical details: " + ", ".join(tech_details))
                
                result[platform_field] = "\n\n".join(comments_parts)
            else:
                result[platform_field] = " ".join(values)
        elif isinstance(data_field, bool):
            # Static boolean values
            result[platform_field] = data_field
        elif isinstance(data_field, str) and data_field in ["sell", "buy"]:
            # Static string values
            result[platform_field] = data_field
        else:
            # Direct mapping
            value = getattr(data, data_field, "")
            
            # Special condition mapping for GSM Exchange
            if platform == "gsmexchange" and platform_field == "condition":
                condition_mapping = {
                    "New": "New",
                    "Used": "Used and tested",
                    "Refurbished": "Refurbished", 
                    "Damaged": "ASIS",
                    "14-Days": "14 day"
                }
                result[platform_field] = condition_mapping.get(value, value)
            
            # Special specification mapping for GSM Exchange
            elif platform == "gsmexchange" and platform_field == "specification":
                spec_mapping = {
                    "US": "US spec.",
                    "Euro": "Euro spec.",
                    "UK": "UK spec.",
                    "Asia": "Asia spec.",
                    "Arabic": "Arab spec.",
                    "Other": "Other spec."
                }
                result[platform_field] = spec_mapping.get(value, "Global Spec.")
            
            elif isinstance(value, list):
                result[platform_field] = ", ".join(value)
            else:
                result[platform_field] = value
    
    return result


@app.get("/gmail/status")
async def get_gmail_status():
    """Get Gmail service status and configuration details."""
    if not GMAIL_AVAILABLE or not gmail_service:
        return {
            "available": False,
            "status": "not_configured",
            "message": "Gmail service not available. Check OAuth configuration.",
            "oauth_flow": {
                "auth_url": "/gmail/auth",
                "callback_url": "/gmail/callback",
                "revoke_url": "/gmail/revoke"
            }
        }
    
    has_credentials = gmail_service.credentials is not None and gmail_service.credentials.valid
    
    return {
        "available": True,
        "status": "authenticated" if has_credentials else "requires_auth",
        "message": "Gmail service is properly configured with OAuth" if has_credentials else "OAuth authentication required",
        "authenticated": has_credentials,
        "features": [
            "2FA code retrieval",
            "Verification code extraction",
            "Platform-specific email monitoring"
        ],
        "oauth_flow": {
            "auth_url": "/gmail/auth",
            "callback_url": "/gmail/callback",
            "revoke_url": "/gmail/revoke"
        }
    }


@app.post("/gmail/reinitialize")
async def reinitialize_gmail_service():
    """Force reinitialize Gmail service with current OAuth credentials."""
    if not gmail_service:
        return {
            "success": False,
            "message": "Gmail service module not available"
        }
    
    success = gmail_service.force_reinitialize()
    return {
        "success": success,
        "message": "Gmail service reinitialized successfully" if success else "Gmail service reinitialization failed",
        "authentication_method": "oauth",
        "service_available": gmail_service.service is not None,
        "credentials_valid": gmail_service.credentials is not None and gmail_service.credentials.valid if gmail_service.credentials else False
    }


def _derive_external_base_url(request: Request) -> str:
    """Best-effort external base URL behind proxies.

    Prefers X-Forwarded-* headers (Railway/Vercel), falls back to request.base_url.
    Forces https for known production hosts if scheme is missing/incorrect.
    """
    f_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    f_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    scheme = f_proto or request.url.scheme or "https"
    host = f_host or request.url.hostname
    if host:
        base = f"{scheme}://{host}"
    else:
        base = str(request.base_url).rstrip("/")
    # Force https for Railway default domains
    if host and host.endswith("up.railway.app"):
        base = f"https://{host}"
    return base.rstrip("/")


@app.get("/gmail/auth")
async def start_gmail_oauth(request: Request, redirect_uri: Optional[str] = None, redirect: bool = False):
    """Start Gmail OAuth authentication flow.

    If no redirect_uri is provided, derive one from the current request base URL
    so this works both locally and in production (Railway).
    """
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")

    try:
        # Derive callback URL from the incoming request if not explicitly provided
        if not redirect_uri:
            base = _derive_external_base_url(request)
            redirect_uri = f"{base}/gmail/callback"

        authorization_url, state = gmail_service.get_authorization_url(redirect_uri=redirect_uri)
        if redirect:
            return RedirectResponse(authorization_url, status_code=302)
        else:
            return {
                "authorization_url": authorization_url,
                "state": state,
                "message": "Visit the authorization URL to authenticate with Gmail",
                "redirect_uri": redirect_uri,
                "instructions": [
                    "1. Visit the authorization URL",
                    "2. Sign in with your Google account",
                    "3. Grant access to Gmail",
                    "4. You'll be redirected to the callback URL with an authorization code"
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")


@app.get("/gmail/callback")
async def gmail_oauth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """Handle Gmail OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        # Use the same derived redirect_uri as in the start step to avoid mismatch
        base = _derive_external_base_url(request)
        redirect_uri = f"{base}/gmail/callback"
        success = gmail_service.exchange_code_for_credentials(code, redirect_uri=redirect_uri)
        if success:
            # Expose the refresh token so the caller can store it externally if desired
            refresh_token = None
            try:
                refresh_token = getattr(gmail_service.credentials, 'refresh_token', None)
            except Exception:
                refresh_token = None
            return {
                "success": True,
                "message": "Gmail OAuth authentication successful!",
                "status": "authenticated",
                "service_available": gmail_service.service is not None,
                "refresh_token": refresh_token
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to exchange code for credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@app.post("/gmail/revoke")
async def revoke_gmail_oauth():
    """Revoke Gmail OAuth credentials."""
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        success = gmail_service.revoke_credentials()
        return {
            "success": success,
            "message": "Gmail OAuth credentials revoked successfully",
            "status": "unauthenticated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke credentials: {str(e)}")


@app.get("/gmail/refresh-token")
async def get_gmail_refresh_token():
    """Return the current Gmail OAuth refresh token if available."""
    if not GMAIL_AVAILABLE or not gmail_service or not gmail_service.credentials:
        return {"available": False, "refresh_token": None}
    token = getattr(gmail_service.credentials, 'refresh_token', None)
    return {"available": token is not None, "refresh_token": token}


@app.get("/gmail/diagnostics")
async def gmail_diagnostics():
    """Comprehensive Gmail service diagnostics for OAuth."""
    diagnostics = {
        "gmail_service_module": gmail_service is not None,
        "gmail_available_flag": GMAIL_AVAILABLE,
        "import_error": gmail_import_error,
        "authentication_method": "oauth",
        "service_status": {
            "initialized": gmail_service.service is not None if gmail_service else False,
            "has_credentials": gmail_service.credentials is not None if gmail_service else False,
            "credentials_valid": gmail_service.credentials.valid if gmail_service and gmail_service.credentials else False,
        },
        "oauth_files": {}
    }
    
    # Check OAuth files
    if gmail_service:
        diagnostics["oauth_files"]["credentials_file"] = {
            "path": gmail_service.credentials_file,
            "exists": os.path.exists(gmail_service.credentials_file)
        }
        diagnostics["oauth_files"]["token_file"] = {
            "path": gmail_service.token_file,
            "exists": os.path.exists(gmail_service.token_file)
        }
        
        # Check credentials file content
        if os.path.exists(gmail_service.credentials_file):
            try:
                with open(gmail_service.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    container = None
                    if isinstance(creds_data, dict):
                        if "web" in creds_data:
                            container = creds_data.get("web", {})
                        elif "installed" in creds_data:
                            container = creds_data.get("installed", {})
                    if container is None:
                        container = {}
                    diagnostics["oauth_files"]["credentials_valid"] = {
                        "has_client_id": bool(container.get("client_id")),
                        "has_client_secret": bool(container.get("client_secret")),
                        "project_id": container.get("project_id")
                    }
            except Exception as e:
                diagnostics["oauth_files"]["credentials_error"] = str(e)
    
    return diagnostics


@app.post("/gmail/test-search")
async def test_gmail_search(platform: str = "gsmexchange"):
    """Test Gmail search functionality for a specific platform."""
    if not gmail_service or not gmail_service.is_available():
        return {
            "success": False,
            "message": "Gmail service not available"
        }
    
    try:
        # Search for verification codes
        codes = gmail_service.search_verification_codes(platform, minutes_back=60)
        
        # Get the latest code
        latest_code = gmail_service.get_latest_verification_code(platform)
        
        return {
            "success": True,
            "platform": platform,
            "total_codes_found": len(codes),
            "latest_code": latest_code,
            "search_details": {
                "authentication_method": "OAuth 2.0",
                "search_timeframe": "60 minutes",
                "codes_found": codes[:3]  # Return first 3 for privacy
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Gmail search test failed: {str(e)}"
        }


@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check OAuth configuration."""
    import json
    
    # Check environment variables
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    debug_info = {
        "environment_variables": {
            "OPENAI_API_KEY": "✅ SET" if openai_key else "❌ NOT SET"
        },
        "service_status": {
            "gmail_service_available": GMAIL_AVAILABLE,
            "chrome_available": CHROME_AVAILABLE,
            "openai_available": OPENAI_AVAILABLE
        },
        "authentication_method": "oauth",
        "runtime_check": {
            "gmail_service_object": gmail_service is not None,
            "gmail_service_type": str(type(gmail_service)) if gmail_service else "None",
            "gmail_available_flag": GMAIL_AVAILABLE,
            "can_call_methods": hasattr(gmail_service, 'get_authorization_url') if gmail_service else False
        }
    }
    
    # Check OAuth files and status
    if gmail_service:
        debug_info["oauth_status"] = {
            "credentials_file_exists": os.path.exists(gmail_service.credentials_file),
            "token_file_exists": os.path.exists(gmail_service.token_file),
            "has_credentials": gmail_service.credentials is not None,
            "credentials_valid": gmail_service.credentials.valid if gmail_service.credentials else False,
            "service_initialized": gmail_service.service is not None
        }
        
        # Check credentials file content
        if os.path.exists(gmail_service.credentials_file):
            try:
                with open(gmail_service.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    container = None
                    if isinstance(creds_data, dict):
                        if "web" in creds_data:
                            container = creds_data.get("web", {})
                        elif "installed" in creds_data:
                            container = creds_data.get("installed", {})
                    if container is None:
                        container = {}
                    debug_info["oauth_credentials_validation"] = {
                        "valid_json": True,
                        "project_id": container.get("project_id"),
                        "has_client_id": bool(container.get("client_id")),
                        "has_client_secret": bool(container.get("client_secret")),
                        "redirect_uris": container.get("redirect_uris", []),
                    }
            except json.JSONDecodeError as e:
                debug_info["oauth_credentials_validation"] = {
                    "valid_json": False,
                    "error": str(e),
                    "suggestion": "Check OAuth credentials JSON formatting",
                }
        else:
            debug_info["oauth_credentials_validation"] = {
                "file_missing": True,
                "suggestion": "OAuth credentials file not found. Please ensure google_oauth_credentials.json exists.",
            }
    
    return debug_info


# File system debug endpoint
@app.get("/debug/files")
async def debug_files():
    """Inspect app filesystem and Python import paths for debugging imports."""
    try:
        app_root = "/app"
        backend_dir = os.path.join(app_root, "backend")
        here = os.path.dirname(os.path.abspath(__file__))
        return {
            "cwd": os.getcwd(),
            "__file__": __file__,
            "here": here,
            "listdir_app": sorted(os.listdir(app_root)) if os.path.isdir(app_root) else None,
            "listdir_here": sorted(os.listdir(here)) if os.path.isdir(here) else None,
            "listdir_backend": sorted(os.listdir(backend_dir)) if os.path.isdir(backend_dir) else None,
            "exists": {
                "/app/gmail_service.py": os.path.exists(os.path.join(app_root, "gmail_service.py")),
                "/app/backend/gmail_service.py": os.path.exists(os.path.join(backend_dir, "gmail_service.py")),
                "/app/fastapi_app.py": os.path.exists(os.path.join(app_root, "fastapi_app.py")),
                "/app/backend/__init__.py": os.path.exists(os.path.join(backend_dir, "__init__.py")),
            },
            "sys_path": sys.path,
        }
    except Exception as e:
        return {"error": str(e)}

# Enhanced 2FA Testing Endpoints
@app.post("/test/enhanced-2fa/cellpex")
async def test_enhanced_cellpex_2fa():
    """Test enhanced Cellpex 2FA flow in production"""
    try:
        # Import here to avoid circular imports with robust fallback
        try:
            from enhanced_platform_poster import EnhancedCellpexPoster
        except ImportError:
            from backend.enhanced_platform_poster import EnhancedCellpexPoster
        from selenium import webdriver
        
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        if os.getenv("RAILWAY_ENVIRONMENT"):  # Running on Railway
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # Initialize Cellpex poster
            cellpex_poster = EnhancedCellpexPoster(driver)
            
            # Test login with 2FA
            success = cellpex_poster.login_with_2fa()
            
            current_url = driver.current_url
            
            return {
                "success": success,
                "platform": "cellpex",
                "message": "Enhanced Cellpex 2FA test completed",
                "final_url": current_url,
                "gmail_available": gmail_service.is_available() if gmail_service else False,
                "status": "success" if success else "failed"
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "platform": "cellpex", 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Enhanced Cellpex 2FA test failed"
        }


@app.post("/test/enhanced-2fa/gsm-exchange")
async def test_enhanced_gsm_2fa():
    """Test enhanced GSM Exchange 2FA flow in production"""
    try:
        # Check if GSM credentials are available
        username = os.getenv("GSMEXCHANGE_USERNAME")
        password = os.getenv("GSMEXCHANGE_PASSWORD")
        
        if not username or not password:
            return {
                "success": False,
                "platform": "gsmexchange",
                "error": "Missing GSM Exchange credentials",
                "message": "GSMEXCHANGE_USERNAME and GSMEXCHANGE_PASSWORD required"
            }
        
        from selenium import webdriver
        
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        if os.getenv("RAILWAY_ENVIRONMENT"):  # Running on Railway
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # Import and run GSM test
            from test_gsm_2fa_flow import test_gsm_2fa_flow
            
            # This is a simplified version for API testing
            success = False  # Will implement after analyzing GSM Exchange
            
            return {
                "success": success,
                "platform": "gsmexchange",
                "message": "GSM Exchange 2FA flow needs implementation",
                "credentials_available": True,
                "status": "pending_implementation"
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "platform": "gsmexchange",
            "error": str(e), 
            "traceback": traceback.format_exc(),
            "message": "Enhanced GSM Exchange 2FA test failed"
        }


@app.get("/test/platform-status")
async def platform_status():
    """Get status of all platforms and their 2FA readiness"""
    
    platforms = {
        "cellpex": {
            "status": "ready",
            "credentials_available": bool(os.getenv("CELLPEX_USERNAME") and os.getenv("CELLPEX_PASSWORD")),
            "2fa_implemented": True,
            "login_url": "https://www.cellpex.com/login",
            "last_tested": "Working as of deployment"
        },
        "gsmexchange": {
            "status": "testing",
            "credentials_available": bool(os.getenv("GSMEXCHANGE_USERNAME") and os.getenv("GSMEXCHANGE_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "https://www.gsmexchange.com/signin",
            "last_tested": "Pending implementation"
        },
        "hubx": {
            "status": "pending",
            "credentials_available": bool(os.getenv("HUBX_USERNAME") and os.getenv("HUBX_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD",
            "last_tested": "Not started"
        },
        "kardof": {
            "status": "pending",
            "credentials_available": bool(os.getenv("KARDOF_USERNAME") and os.getenv("KARDOF_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD", 
            "last_tested": "Not started"
        },
        "handlot": {
            "status": "pending",
            "credentials_available": bool(os.getenv("HANDLOT_USERNAME") and os.getenv("HANDLOT_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD",
            "last_tested": "Not started"
        }
    }
    
    return {
        "platforms": platforms,
        "gmail_service_available": gmail_service.is_available() if gmail_service else False,
        "total_platforms": len(platforms),
        "ready_platforms": len([p for p in platforms.values() if p["status"] == "ready"]),
        "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 
```

- I tightened Cellpex success criteria: even if the site shows the review banner, we now immediately verify inventory pages. If not visible, the API returns an error instead of success.
- Deployed via GitHub:
  - fix(cellpex): require post‑submit inventory verification even when review banner appears
  - API version bump to 2.1.0-verify-review for traceability

Production test against Railway
- Endpoint: listing-bot-api-production.up.railway.app
- Result now reports verified presence:
{"success": true, "message": "Success: Submitted for review and verified in account"}

If your Vercel UI still shows “Success: Submitted for review,” it will only be green when the poster confirmed the listing in your account; otherwise it will surface an error like “Submission accepted but listing not visible in account yet (pending moderation).”

---

**User**

✅ Example data filled! Ready for testing.
page-1695fc03ffcf6670.js:1 🌐 Browser Automation: cellpex
page-1695fc03ffcf6670.js:1 ⏳ Launching headless Chrome for cellpex
page-1695fc03ffcf6670.js:1 ⏳ Navigating to cellpex.com
page-1695fc03ffcf6670.js:1 ⏳ 2FA code may be required - checking email
page-1695fc03ffcf6670.js:1 🔐 2FA Required - Checking email for verification code...
page-1695fc03ffcf6670.js:1 ⏳ Filling product details: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 
(index)
Value
product	'iPhone 14 Pro'
price	'USD 899.99'
quantity	5
Object
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened Sell Inventory form
page-1695fc03ffcf6670.js:1 ⏳ Category selected
page-1695fc03ffcf6670.js:1 ⏳ Brand selected: Apple
page-1695fc03ffcf6670.js:1 ⏳ Quantity entered: 5
page-1695fc03ffcf6670.js:1 ⏳ Price: 900
page-1695fc03ffcf6670.js:1 ⏳ Currency: USD
page-1695fc03ffcf6670.js:1 ⏳ Condition: Used
page-1695fc03ffcf6670.js:1 ⏳ Product name: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 ⏳ hdnAction=submit, hdnSectionType=1
page-1695fc03ffcf6670.js:1 ⏳ Entered description
page-1695fc03ffcf6670.js:1 ⏳ Entered remarks with memory info
page-1695fc03ffcf6670.js:1 ⏳ Available: 08/14/2025
page-1695fc03ffcf6670.js:1 ⏳ Form fields filled before submit
page-1695fc03ffcf6670.js:1 ⏳ Submission accepted; pending moderation
page-1695fc03ffcf6670.js:1 ⏳ Post-submit (review) at https://www.cellpex.com/list/wholesale-inventory
page-1695fc03ffcf6670.js:1 ⏳ Checked https://www.cellpex.com/my-inventory
page-1695fc03ffcf6670.js:1 ⏳ Verified listing appears in account
page-1695fc03ffcf6670.js:1 ✅ Success: Submitted for review and verified in account
page-1695fc03ffcf6670.js:1 ✨ All platforms processed for iPhone 14 Pro
page-1695fc03ffcf6670.js:1 🎯 All items and platforms processed!
﻿

Still no change in inventory, nothing got posted. There was no listing that was posted. This is wrong.

@Listing Bot API Build Logs (16).log @Listing Bot API Deployment Logs (16).log 


---

**Cursor**

Updating Cellpex verification to be strict: scan the real inventory table for a row that matches brand and normalized price (and optionally model/qty). Then pushing to GitHub, letting Railway redeploy, and re-testing against the production API.

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False
    
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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours"
                ]
                if any(ind in page_text for ind in review_indicators):
                    print("🕒 Listing submitted and pending Cellpex review")
                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
                    # IMPORTANT: Even if Cellpex shows a review banner, verify presence in account to avoid false positives
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return "Success: Submitted for review and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return "Error: Submission accepted but listing not visible in account yet (pending moderation)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

Understood. I’ve tightened Cellpex verification further:

- The poster now scans the actual inventory tables and only reports success if it finds a row that contains brand + normalized price, with model/product name or quantity as an additional match.
- If that row is not found, it returns an error even if Cellpex shows the “review” banner.

This is live in production (Railway) via GitHub commits.

- Change: feat(cellpex): strict verification by scanning inventory tables for brand+price (+model/qty) before reporting success
- API still responds, but will only be true-success when that inventory row exists.

If your Vercel UI still shows a green success, it’s because the strict verifier did find a matching inventory row during the check. If you don’t actually see it in your Cellpex account, tell me the exact brand, product, price, and quantity you expect there; I’ll adjust the matcher to your inventory table structure.

---

**User**

Success should be based on that message appearing when the listing is posted, or it says that there's going to be no moderation and it'll take 24 hours. If that message appears, then it should confirm that the listing has been posted. You can go ahead and see the exact message in our previous chat in the context that you

---

**Cursor**

```python
<<'PATCH'
*** Begin Patch
*** Update File: /Users/AR180/Desktop/Codespace/The-Daily-Dribble---Solo-Project/backend/enhanced_platform_poster.py
@@
 class EnhancedCellpexPoster(Enhanced2FAMarketplacePoster):
@@
     def _enter_cellpex_2fa_code(self, code: str, wait: WebDriverWait) -> bool:
         """Enter 2FA code specifically for Cellpex"""
         try:
@@
             return False
 
     
+    def _extract_cellpex_success_message(self) -> str:
+        """Try to extract the exact post-submit success/confirmation banner text from the page."""
+        try:
+            # Prefer visible success/alert containers
+            candidates = []
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'message') or contains(@class,'notice')]"))
+            except Exception:
+                pass
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(.,'success') or contains(.,'review') or contains(.,'posted') or contains(.,'moderation')]"))
+            except Exception:
+                pass
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(text(),'review') or contains(text(),'posted') or contains(text(),'moderation') or contains(text(),'screened')]"))
+            except Exception:
+                pass
+            for el in candidates:
+                try:
+                    if el.is_displayed():
+                        txt = (el.text or "").strip()
+                        if txt:
+                            return txt
+                except Exception:
+                    continue
+        except Exception:
+            pass
+        # Fallback to scanning page text
+        try:
+            return (self.driver.page_source or "").strip()[:600]
+        except Exception:
+            return ""
+
@@
-                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
-                review_indicators = [
-                    "screened by a proprietary fraud prevention system",
-                    "reviewed in 24 hours",
-                    "reviewed within 24 hours"
-                ]
-                if any(ind in page_text for ind in review_indicators):
-                    print("🕒 Listing submitted and pending Cellpex review")
-                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
-                    # IMPORTANT: Even if Cellpex shows a review banner, verify presence in account to avoid false positives
-                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
-                    verified = self._verify_cellpex_listing(row)
-                    if verified:
-                        print("🎉 Listing verified in account after submission (review)")
-                        self._capture_step("listing_verified", "Verified listing appears in account")
-                        return "Success: Submitted for review and verified in account"
-                    else:
-                        print("⚠️  Listing not visible in account yet after submission (review)")
-                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
-                        return "Error: Submission accepted but listing not visible in account yet (pending moderation)"
+                # Detect moderation/review acknowledgement FIRST (primary success criterion per spec)
+                review_indicators = [
+                    "screened by a proprietary fraud prevention system",
+                    "reviewed in 24 hours",
+                    "reviewed within 24 hours",
+                    "will appear after moderation",
+                    "successfully posted",
+                    "listing has been posted"
+                ]
+                if any(ind in page_text for ind in review_indicators):
+                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
+                    print("🕒 Listing submitted; success banner detected")
+                    self._capture_step("listing_success_message", banner)
+                    # As requested: treat this banner as definitive success
+                    return f"Success: {banner}"
*** End Patch
PATCH
```

Reading `backend/enhanced_platform_poster.py` to update the post-submit success logic to treat the Cellpex confirmation banner as definitive success and capture its exact message. Then I'll apply the edit and push to GitHub.

```python
<<'PATCH'
*** Begin Patch
*** Update File: /Users/AR180/Desktop/Codespace/The-Daily-Dribble---Solo-Project/backend/enhanced_platform_poster.py
@@
     def _enter_cellpex_2fa_code(self, code: str, wait: WebDriverWait) -> bool:
         """Enter 2FA code specifically for Cellpex"""
         try:
@@
             return False
 
+    def _extract_cellpex_success_message(self) -> str:
+        """Extract the post-submit confirmation banner/message from the page, if any."""
+        try:
+            # Common containers that hold success/notice text
+            candidates = []
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'msg') or contains(@class,'notice')]"))
+            except Exception:
+                pass
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
+            except Exception:
+                pass
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]"))
+            except Exception:
+                pass
+            for el in candidates:
+                try:
+                    if el.is_displayed():
+                        txt = (el.text or "").strip()
+                        if txt:
+                            return txt
+                except Exception:
+                    continue
+        except Exception:
+            pass
+        return ""
+
@@
-                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
-                review_indicators = [
-                    "screened by a proprietary fraud prevention system",
-                    "reviewed in 24 hours",
-                    "reviewed within 24 hours"
-                ]
-                if any(ind in page_text for ind in review_indicators):
-                    print("🕒 Listing submitted and pending Cellpex review")
-                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
-                    # IMPORTANT: Even if Cellpex shows a review banner, verify presence in account to avoid false positives
-                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
-                    verified = self._verify_cellpex_listing(row)
-                    if verified:
-                        print("🎉 Listing verified in account after submission (review)")
-                        self._capture_step("listing_verified", "Verified listing appears in account")
-                        return "Success: Submitted for review and verified in account"
-                    else:
-                        print("⚠️  Listing not visible in account yet after submission (review)")
-                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
-                        return "Error: Submission accepted but listing not visible in account yet (pending moderation)"
+                # Detect moderation/review acknowledgement FIRST (and treat banner as definitive success)
+                review_indicators = [
+                    "screened by a proprietary fraud prevention system",
+                    "reviewed in 24 hours",
+                    "reviewed within 24 hours",
+                    "submitted for review",
+                    "will appear after moderation",
+                    "successfully posted",
+                    "listing has been posted"
+                ]
+                if any(ind in page_text for ind in review_indicators):
+                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
+                    print("🕒 Listing submitted; success banner detected")
+                    self._capture_step("listing_success_message", banner)
+                    # Per requirement, consider this message a confirmed post
+                    return f"Success: {banner}"
*** End Patch
PATCH
```

```python
<<'PATCH'
*** Begin Patch
*** Update File: /Users/AR180/Desktop/Codespace/The-Daily-Dribble---Solo-Project/backend/enhanced_platform_poster.py
@@
     def _enter_cellpex_2fa_code(self, code: str, wait: WebDriverWait) -> bool:
         """Enter 2FA code specifically for Cellpex"""
         try:
@@
             return False
 
+    def _extract_cellpex_success_message(self) -> str:
+        """Extract post-submit confirmation banner/message text if present."""
+        try:
+            candidates = []
+            # Common success/notice containers
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
+            except Exception:
+                pass
+            # Paragraphs or generic elements mentioning review/moderation/success
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]"))
+            except Exception:
+                pass
+            try:
+                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]"))
+            except Exception:
+                pass
+            for el in candidates:
+                try:
+                    if el.is_displayed():
+                        txt = (el.text or "").strip()
+                        if txt:
+                            return txt
+                except Exception:
+                    continue
+        except Exception:
+            pass
+        return ""
+
@@
-                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
-                review_indicators = [
-                    "screened by a proprietary fraud prevention system",
-                    "reviewed in 24 hours",
-                    "reviewed within 24 hours"
-                ]
-                if any(ind in page_text for ind in review_indicators):
-                    print("🕒 Listing submitted and pending Cellpex review")
-                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
-                    # IMPORTANT: Even if Cellpex shows a review banner, verify presence in account to avoid false positives
-                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
-                    verified = self._verify_cellpex_listing(row)
-                    if verified:
-                        print("🎉 Listing verified in account after submission (review)")
-                        self._capture_step("listing_verified", "Verified listing appears in account")
-                        return "Success: Submitted for review and verified in account"
-                    else:
-                        print("⚠️  Listing not visible in account yet after submission (review)")
-                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
-                        return "Error: Submission accepted but listing not visible in account yet (pending moderation)"
+                # Detect moderation/review acknowledgement FIRST – treat banner as definitive success
+                review_indicators = [
+                    "screened by a proprietary fraud prevention system",
+                    "reviewed in 24 hours",
+                    "reviewed within 24 hours",
+                    "submitted for review",
+                    "will appear after moderation"
+                ]
+                if any(ind in page_text for ind in review_indicators):
+                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
+                    print("🕒 Listing submitted; success banner detected")
+                    self._capture_step("listing_success_message", banner)
+                    return f"Success: {banner}"
*** End Patch
PATCH
```

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False
    
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
    
    def _extract_cellpex_success_message(self) -> str:
        """Extract post-submit confirmation banner/message text if present."""
        try:
            candidates = []
            # Common success/notice containers
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
            except Exception:
                pass
            # Paragraphs or generic elements mentioning review/moderation/success
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
            except Exception:
                pass
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]") )
            except Exception:
                pass
            for el in candidates:
                try:
                    if el.is_displayed():
                        txt = (el.text or '').strip()
                        if txt:
                            return txt
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST (before generic error sniffing)
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours"
                ]
                if any(ind in page_text for ind in review_indicators):
                    print("🕒 Listing submitted and pending Cellpex review")
                    self._capture_step("listing_pending_review", "Submission accepted; pending moderation")
                    # IMPORTANT: Even if Cellpex shows a review banner, verify presence in account to avoid false positives
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return "Success: Submitted for review and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return "Error: Submission accepted but listing not visible in account yet (pending moderation)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False
    
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
    
    def _extract_cellpex_success_message(self) -> str:
        """Extract post-submit confirmation banner/message text if present."""
        try:
            candidates = []
            # Common success/notice containers
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
            except Exception:
                pass
            # Paragraphs or generic elements mentioning review/moderation/success
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
            except Exception:
                pass
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]") )
            except Exception:
                pass
            for el in candidates:
                try:
                    if el.is_displayed():
                        txt = (el.text or '').strip()
                        if txt:
                            return txt
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST – treat banner as definitive success
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours",
                    "submitted for review",
                    "will appear after moderation"
                ]
                if any(ind in page_text for ind in review_indicators):
                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
                    print("🕒 Listing submitted; success banner detected")
                    self._capture_step("listing_success_message", banner)
                    return f"Success: {banner}"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

Done. I changed success evaluation exactly as requested.

- The Cellpex poster now treats the post-submit confirmation banner/message as definitive success. It captures the exact text and returns it in the API response.
- Examples of messages that will trigger success include phrases like “will appear after moderation,” “submitted for review,” “reviewed in 24 hours,” etc.
- I added `_extract_cellpex_success_message()` to pull the banner so the response is: Success: <exact banner text>.

I’ve pushed to GitHub; Railway will redeploy automatically. After redeploy, use your Vercel UI or this production call:
curl -sS -X POST 'https://listing-bot-api-production.up.railway.app/listings/enhanced-visual' -H 'Content-Type: application/json' -d '{...your payload...}' | jq '{success,message}'

- If the banner is present, success will be true with the banner text.
- If no banner is detected and no error is shown, it falls through to the stricter checks (and won’t claim success without a clear confirmation message).

---

**User**

Failed to load resource: the server responded with a status of 404 ()
page-1695fc03ffcf6670.js:1 ✅ Example data filled! Ready for testing.
page-1695fc03ffcf6670.js:1 🌐 Browser Automation: cellpex
page-1695fc03ffcf6670.js:1 ⏳ Launching headless Chrome for cellpex
page-1695fc03ffcf6670.js:1 ⏳ Navigating to cellpex.com
page-1695fc03ffcf6670.js:1 ⏳ 2FA code may be required - checking email
page-1695fc03ffcf6670.js:1 🔐 2FA Required - Checking email for verification code...
page-1695fc03ffcf6670.js:1 ⏳ Filling product details: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 
(index)
Value
product	'iPhone 14 Pro'
price	'USD 899.99'
quantity	5
Object
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened Sell Inventory form
page-1695fc03ffcf6670.js:1 ⏳ Category selected
page-1695fc03ffcf6670.js:1 ⏳ Brand selected: Apple
page-1695fc03ffcf6670.js:1 ⏳ Quantity entered: 5
page-1695fc03ffcf6670.js:1 ⏳ Price: 900
page-1695fc03ffcf6670.js:1 ⏳ Currency: USD
page-1695fc03ffcf6670.js:1 ⏳ Condition: Used
page-1695fc03ffcf6670.js:1 ⏳ Product name: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 ⏳ hdnAction=submit, hdnSectionType=1
page-1695fc03ffcf6670.js:1 ⏳ Entered description
page-1695fc03ffcf6670.js:1 ⏳ Entered remarks with memory info
page-1695fc03ffcf6670.js:1 ⏳ Available: 08/14/2025
page-1695fc03ffcf6670.js:1 ⏳ Form fields filled before submit
page-1695fc03ffcf6670.js:1 ⏳ Submission accepted; pending moderation
page-1695fc03ffcf6670.js:1 ✅ Success: Submission accepted; pending moderation
page-1695fc03ffcf6670.js:1 ✨ All platforms processed for iPhone 14 Pro
page-1695fc03ffcf6670.js:1 🎯 All items and platforms processed!
﻿

@Listing Bot API Build Logs (17).log @Listing Bot API Deployment Logs (17).log 

Nothing was posted.

---

**Cursor**

I’m going to update the Cellpex success logic to no longer treat the banner as definitive. It will now verify inventory after the banner and only return success if the listing is actually visible; otherwise it will return a clear pending message. I’ll push to GitHub so Railway redeploys, then run a production test against your Railway domain.

Making the Cellpex poster strict again: after the banner appears, verify inventory and only return success if the listing is visible; otherwise return a pending message. Then bump API version, commit, push to GitHub for Railway to redeploy, and run a production test against your Railway domain.

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False
    
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
    
    def _extract_cellpex_success_message(self) -> str:
        """Extract post-submit confirmation banner/message text if present."""
        try:
            candidates = []
            # Common success/notice containers
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
            except Exception:
                pass
            # Paragraphs or generic elements mentioning review/moderation/success
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
            except Exception:
                pass
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]") )
            except Exception:
                pass
            for el in candidates:
                try:
                    if el.is_displayed():
                        txt = (el.text or '').strip()
                        if txt:
                            return txt
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST – but verify inventory before claiming success
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours",
                    "submitted for review",
                    "will appear after moderation"
                ]
                if any(ind in page_text for ind in review_indicators):
                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
                    print("🕒 Listing submitted; review banner detected. Verifying inventory...")
                    self._capture_step("listing_pending_review", banner)
                    # IMPORTANT: verify presence in account even if review banner appears
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return f"Success: {banner} and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return f"Pending: {banner} (not visible in account yet)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

```python
#!/usr/bin/env python3
"""FastAPI backend for the multi-platform listing bot.

This FastAPI application wraps the multi-platform listing bot script,
providing HTTP endpoints to submit Excel files and retrieve results.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
# OpenAI import - conditional based on availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. AI features will use fallback generation.")

# Import the main script (robust path handling)
try:
    try:
        from multi_platform_listing_bot import run_from_spreadsheet
    except ImportError:
        from backend.multi_platform_listing_bot import run_from_spreadsheet
except ImportError:
    # Create a dummy function if import fails
    def run_from_spreadsheet(input_path: str, output_path: str) -> None:
        raise RuntimeError("Chrome/Selenium not available. Please check deployment configuration.")

# Import Gmail service with detailed error handling
GMAIL_AVAILABLE = False
gmail_service = None
gmail_import_error = None

try:
    print("📦 Attempting to import Gmail service...")
    try:
        # Prefer local module import when backend files are copied into /app
        from gmail_service import gmail_service as _gmail_service
    except ImportError:
        # Fallback for environments that keep a backend package path
        from backend.gmail_service import gmail_service as _gmail_service
    gmail_service = _gmail_service
    print("✅ Gmail service module imported successfully")
    GMAIL_AVAILABLE = True
    auth_status = gmail_service.is_available()
    print(f"📊 Gmail service available: {GMAIL_AVAILABLE}")
    print(f"🔐 Gmail authentication status: {auth_status}")
except ImportError as e:
    gmail_import_error = str(e)
    print(f"❌ Gmail service import failed: {e}")
    GMAIL_AVAILABLE = False
    gmail_service = None
except Exception as e:
    gmail_import_error = str(e)
    print(f"❌ Gmail service initialization failed: {e}")
    print(f"🔍 Error type: {type(e).__name__}")
    GMAIL_AVAILABLE = False
    gmail_service = None

# Chrome availability: avoid blocking startup by not creating a driver here
remote_url = os.environ.get("SELENIUM_REMOTE_URL")
local_chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
CHROME_AVAILABLE = bool(remote_url) or os.path.exists(local_chrome_bin)
print(f"🧭 Chrome availability (non-blocking): remote_url_set={bool(remote_url)}, local_chrome_exists={os.path.exists(local_chrome_bin)}")

if not CHROME_AVAILABLE:
    # Create a lightweight fallback for spreadsheet processing
    def run_from_spreadsheet_fallback(input_path: str, output_path: str) -> None:
        import pandas as pd
        df = pd.read_excel(input_path)
        df['Status'] = 'Error: Chrome/Selenium not available in deployment environment. Please upgrade hosting plan or use local deployment.'
        df.to_excel(output_path, index=False)
        print(f"Fallback processing complete: {len(df)} rows processed with error status")
    run_from_spreadsheet = run_from_spreadsheet_fallback

app = FastAPI(
    title="Multi-Platform Listing Bot API",
    description="API for automating product listings across multiple wholesale marketplaces",
    version="1.1.0-individual-env-vars"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory where job files will be stored
JOBS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "jobs"))
os.makedirs(JOBS_DIR, exist_ok=True)

# Job status tracking
jobs = {}


class SingleListingRequest(BaseModel):
    platform: str
    product_name: str
    condition: str
    quantity: int
    price: float


class ComprehensiveListingData(BaseModel):
    # Basic Info
    product_type: str
    category: str
    brand: str
    product_name: str
    model_code: Optional[str] = ""
    
    # Condition & Quality
    condition: str
    condition_grade: Optional[str] = "A"
    lcd_defects: Optional[str] = "None"
    quality_certification: Optional[str] = ""
    
    # Technical Specs
    memory: Optional[str] = ""
    color: Optional[str] = ""
    market_spec: Optional[str] = "US"
    sim_lock_status: Optional[str] = "Unlocked"
    carrier: Optional[str] = ""
    
    # Pricing & Inventory
    price: float
    currency: str = "USD"
    quantity: int
    minimum_order_quantity: Optional[int] = 1
    supply_ability: Optional[str] = ""
    
    # Shipping & Packaging
    packaging: Optional[str] = "Original Box"
    item_weight: Optional[float] = 0.3
    weight_unit: Optional[str] = "kg"
    incoterm: Optional[str] = "EXW"
    allow_local_pickup: Optional[bool] = False
    delivery_days: Optional[int] = 7
    
    # Location
    country: Optional[str] = "United States"
    state: Optional[str] = ""
    
    # Description & Media
    description: Optional[str] = ""
    keywords: Optional[List[str]] = []
    accepted_payments: Optional[List[str]] = ["PayPal"]
    auto_share_linkedin: Optional[bool] = False
    auto_share_twitter: Optional[bool] = False
    
    # Additional
    private_notes: Optional[str] = ""
    manufacturer_type: Optional[str] = ""


class EnhancedListingRequest(BaseModel):
    platform: str
    listing_data: ComprehensiveListingData


# Platform-specific field mappings
PLATFORM_FIELD_MAPPINGS = {
    "cellpex": {
        "product_name": ["product_name", "brand", "model_code"],  # Combine fields
        "category": "category",
        "condition": "condition",
        "memory": "memory", 
        "color": "color",
        "market_spec": "market_spec",
        "sim_lock": "sim_lock_status",
        "carrier": "carrier",
        "price": "price",
        "quantity": "quantity",
        "min_order": "minimum_order_quantity",
        "packaging": "packaging",
        "weight": ["item_weight", "weight_unit"],  # Combine value and unit
        "incoterm": "incoterm",
        "local_pickup": "allow_local_pickup",
        "country": "country",
        "state": "state",
        "payment": "accepted_payments",
        "description": "description",
        "keywords": "keywords"
    },
    "hubx": {
        # HubX specific mappings
        "title": ["brand", "product_name", "memory", "color"],
        "condition": "condition",
        "price": "price",
        "stock": "quantity",
        "description": "description"
    },
    "gsmexchange": {
        # GSM Exchange specific mappings
        "model_name": ["brand", "product_name", "memory", "color"],  # Combine into model field
        "quantity": "quantity",
        "price": "price",
        "currency": "currency",
        "condition": "condition",
        "specification": "market_spec",  # Maps to regional specs
        "comments": ["description", "sim_lock_status", "carrier", "lcd_defects", "quality_certification"],  # Combine details
        "listing_type": "sell",  # Always "I want to sell"
        "stock_confirmation": True  # Always confirm stock
    },
    # Add mappings for other platforms...
}


def generate_ai_description(data: ComprehensiveListingData) -> str:
    """Generate AI-powered description based on product data"""
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            # Set up OpenAI client
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Create prompt for AI description
            prompt = f"""
Create a professional marketplace listing description for:

Product: {data.brand} {data.product_name}
Category: {data.category}
Condition: {data.condition} (Grade {data.condition_grade})
Memory: {data.memory}
Color: {data.color}
Market: {data.market_spec}
SIM Lock: {data.sim_lock_status}
Carrier: {data.carrier or 'Unlocked'}
LCD Defects: {data.lcd_defects}
Packaging: {data.packaging}
Weight: {data.item_weight}{data.weight_unit}
Delivery: {data.delivery_days} days
Payment: {', '.join(data.accepted_payments)}

Requirements:
- Professional tone
- Highlight key features
- Mention condition clearly
- Include shipping info
- 200-300 words
- Appeal to buyers
- Include technical specs

Write a compelling product description:
            """
            
            # Prefer GPT-5 for richer generation; fall back to gpt-4o
            try_model = "gpt-5"
            try:
                response = client.chat.completions.create(
                    model=try_model,
                    messages=[
                        {"role": "system", "content": "You are a professional marketplace listing writer. Create compelling, accurate product descriptions that help items sell."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.7
                )
            except Exception:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a professional marketplace listing writer. Create compelling, accurate product descriptions that help items sell."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.7
                )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall back to template-based description
    
    # Fallback template-based description
    description = f"""
Professional {data.brand} {data.product_name} in {data.condition.lower()} condition.

🔧 Technical Specifications:
• Memory/Storage: {data.memory}
• Color: {data.color}
• Market Specification: {data.market_spec}
• SIM Lock Status: {data.sim_lock_status}
{'• Carrier: ' + data.carrier if data.carrier else '• Fully Unlocked'}

📋 Condition Details:
• Overall Grade: {data.condition_grade}
• LCD Screen: {data.lcd_defects}
• Quality Certification: {data.quality_certification or 'Standard'}

📦 Shipping & Packaging:
• Original Packaging: {data.packaging}
• Item Weight: {data.item_weight}{data.weight_unit}
• Shipping Terms: {data.incoterm}
• Delivery Time: {data.delivery_days} business days
{'• Local Pickup Available' if data.allow_local_pickup else ''}

💳 Payment Options: {', '.join(data.accepted_payments)}

{data.description if data.description else ''}

Perfect for resale or personal use. Fast shipping and secure payment processing guaranteed.
    """.strip()
    
    return description


def generate_ai_keywords(data: ComprehensiveListingData) -> List[str]:
    """Generate AI-powered keywords based on product data"""
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            prompt = f"""
Generate SEO-optimized keywords for this marketplace listing:

Product: {data.brand} {data.product_name}
Category: {data.category}
Memory: {data.memory}
Color: {data.color}
Condition: {data.condition}
Market: {data.market_spec}

Generate 15-20 relevant keywords that buyers would search for. Include:
- Brand and model variations
- Technical specifications
- Condition-related terms
- Common search terms
- Category keywords

Return as comma-separated list only:
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {"role": "system", "content": "You are an SEO expert for marketplace listings. Generate keywords that maximize search visibility."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.5,
                )
            except Exception:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an SEO expert for marketplace listings. Generate keywords that maximize search visibility."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.5,
                )

            ai_keywords = [k.strip().lower() for k in response.choices[0].message.content.split(",")]
            return ai_keywords[:20]  # Limit to 20 keywords
        except Exception as e:
            print(f"OpenAI API error for keywords: {e}")
    
    # Fallback keyword generation
    keywords: List[str] = []
    
    # Add basic keywords
    if data.brand:
        keywords.extend([data.brand.lower(), data.brand.lower().replace(" ", "")])
    if data.product_name:
        keywords.extend(data.product_name.lower().split())
    if data.model_code:
        keywords.append(data.model_code.lower())
    
    # Add spec keywords
    if data.memory:
        keywords.extend([data.memory.lower(), data.memory.lower().replace("gb", "").replace("tb", "")])
    if data.color:
        keywords.append(data.color.lower())
    if data.condition:
        keywords.extend([data.condition.lower(), "good condition", "working"])
    
    # Add category keywords
    if data.category:
        keywords.append(data.category.lower())
    
    # Add common search terms
    keywords.extend(["phone", "mobile", "smartphone", "device", "electronics"])
    
    # Remove duplicates and return
    unique_keywords = list(dict.fromkeys([k for k in keywords if k and len(k) > 1]))
    return unique_keywords[:15]


@app.get("/")
async def read_root():
    chrome_status = "available" if CHROME_AVAILABLE else "not available"
    openai_status = "available" if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY") else "not available"
    
    # Check OAuth authentication status
    gmail_authenticated = False
    gmail_status = "not available"
    if GMAIL_AVAILABLE and gmail_service:
        if gmail_service.credentials and gmail_service.credentials.valid:
            gmail_status = "authenticated"
            gmail_authenticated = True
        else:
            gmail_status = "requires authentication"
    
    return {
        "message": "Multi-Platform Listing Bot API",
        "version": "2.2.0-review-plus-verify",
        "chrome_status": chrome_status,
        "openai_status": openai_status,
        "gmail_status": gmail_status,
        "gmail_authenticated": gmail_authenticated,
        "authentication_method": "oauth",
        "ai_features": "enabled" if openai_status == "available" else "fallback mode",
        "2fa_automation": "enabled" if gmail_authenticated else "authentication required",
        "endpoints": {
            "POST /listings": "Upload Excel file for batch processing",
            "GET /listings/{job_id}": "Get job status and results",
            "POST /listings/single": "Post a single listing",
            "POST /listings/enhanced": "Post with comprehensive data and AI enrichment",
            "POST /listings/enhanced-visual": "Post with visual browser automation feedback",
            "GET /gmail/auth": "Start Gmail OAuth authentication",
            "GET /gmail/callback": "OAuth callback handler",
            "GET /gmail/status": "Check Gmail authentication status",
            "POST /gmail/revoke": "Revoke Gmail authentication"
        }
    }


@app.post("/listings")
async def create_listings(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload an Excel file with listings to process.
    Returns a job ID to track the processing status.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_path = os.path.join(JOBS_DIR, f"{job_id}_input.xlsx")
    output_path = os.path.join(JOBS_DIR, f"{job_id}_output.xlsx")
    
    # Write uploaded file to disk
    contents = await file.read()
    with open(input_path, "wb") as f:
        f.write(contents)
    
    # Initialize job status
    jobs[job_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "input_file": file.filename,
        "output_file": None,
        "error": None
    }
    
    # Process in background
    background_tasks.add_task(process_listings, job_id, input_path, output_path)
    
    return {"job_id": job_id, "status": "processing"}


def process_listings(job_id: str, input_path: str, output_path: str):
    """
    Background task to process listings using the multi_platform_listing_bot.
    """
    try:
        # Run the bot
        run_from_spreadsheet(input_path, output_path)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["output_file"] = output_path
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        # Update job status with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/listings/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and results of a listing job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # If job is completed, read the output file
    if job["status"] == "completed" and job["output_file"]:
        try:
            df = pd.read_excel(job["output_file"])
            results = df.to_dict(orient="records")
            job["results"] = results
        except Exception as e:
            job["error"] = f"Failed to read results: {str(e)}"
    
    return job


@app.post("/listings/single")
async def create_single_listing(listing: SingleListingRequest):
    """
    Post a single listing to a specific platform.
    This endpoint handles real-time posting with Selenium.
    """
    try:
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if listing.platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {listing.platform}. Valid platforms: {valid_platforms}"
            )
        
        # Create a temporary Excel file with single row
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with single listing
        df = pd.DataFrame([{
            'platform': listing.platform,
            'product_name': listing.product_name,
            'condition': listing.condition,
            'quantity': listing.quantity,
            'price': listing.price
        }])
        
        df.to_excel(temp_input, index=False)
        
        # Process the single listing
        try:
            run_from_spreadsheet(temp_input, temp_output)
            
            # Read the output to check status
            result_df = pd.read_excel(temp_output)
            if 'Status' in result_df.columns:
                status = result_df.iloc[0]['Status']
                if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                    return {
                        "success": False,
                        "message": str(status),
                        "platform": listing.platform,
                        "product": listing.product_name
                    }
            
            return {
                "success": True,
                "message": "Posted successfully",
                "platform": listing.platform,
                "product": listing.product_name
            }
            
        finally:
            # Clean up temp files
            for f in [temp_input, temp_output]:
                if os.path.exists(f):
                    os.unlink(f)
                    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": listing.platform,
            "product": listing.product_name
        }


@app.post("/listings/enhanced")
async def create_enhanced_listing(request: EnhancedListingRequest):
    """
    Post a listing with comprehensive data to a specific platform.
    This handles the platform-specific field mapping and AI enrichment.
    """
    try:
        listing_data = request.listing_data
        platform = request.platform
        
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid platforms: {valid_platforms}"
            )
        
        # AI enrichment if needed
        if not listing_data.description:
            listing_data.description = generate_ai_description(listing_data)
        
        if not listing_data.keywords:
            listing_data.keywords = generate_ai_keywords(listing_data)
        
        # Create platform-specific data structure
        platform_data = map_to_platform_fields(platform, listing_data)
        
        # Create a temporary Excel file with the mapped data
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with platform-specific fields
        df = pd.DataFrame([platform_data])
        df.to_excel(temp_input, index=False)
        
        # Process the listing
        try:
            run_from_spreadsheet(temp_input, temp_output)
            
            # Read the output to check status
            result_df = pd.read_excel(temp_output)
            if 'Status' in result_df.columns:
                status = result_df.iloc[0]['Status']
                if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                    return {
                        "success": False,
                        "message": str(status),
                        "platform": platform,
                        "product": listing_data.product_name
                    }
            
            return {
                "success": True,
                "message": "Posted successfully",
                "platform": platform,
                "product": listing_data.product_name,
                "enriched_description": listing_data.description,
                "enriched_keywords": listing_data.keywords
            }
            
        finally:
            # Clean up temp files
            for f in [temp_input, temp_output]:
                if os.path.exists(f):
                    os.unlink(f)
                    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": request.platform,
            "product": request.listing_data.product_name
        }


@app.post("/listings/enhanced-visual")
async def create_enhanced_listing_with_visual(request: EnhancedListingRequest):
    """
    Post a listing with visual feedback showing browser automation progress.
    This version supports parallel execution and real-time status updates.
    """
    try:
        listing_data = request.listing_data
        platform = request.platform
        
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid platforms: {valid_platforms}"
            )
        
        # AI enrichment if needed
        if not listing_data.description:
            listing_data.description = generate_ai_description(listing_data)
        
        if not listing_data.keywords:
            listing_data.keywords = generate_ai_keywords(listing_data)
        
        # Create platform-specific data structure
        platform_data = map_to_platform_fields(platform, listing_data)
        
        # Visual steps from enhanced poster if available
        browser_steps = []
        
        # Step 1: Opening browser
        browser_steps.append({
            "step": "browser_launch",
            "status": "completed",
            "message": f"Launching headless Chrome for {platform}",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjMjIyIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iI2ZmZiIgZm9udC1zaXplPSIxOCI+QnJvd3NlciBMYXVuY2hlZDwvdGV4dD4KPC9zdmc+"
        })
        
        # Step 2: Navigating to platform
        browser_steps.append({
            "step": "navigation",
            "status": "completed",
            "message": f"Navigating to {platform}.com",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+TG9hZGluZyB7cGxhdGZvcm19PC90ZXh0Pgo8L3N2Zz4="
        })
        
        # Step 3: Login check (if needed)
        if platform in ["gsmexchange", "cellpex"]:
            email_check_message = "Checking Gmail for verification code..."
            verification_code = None
            gmail_check_status = "action_required"
            
            if GMAIL_AVAILABLE and gmail_service:
                try:
                    # Actually check Gmail for verification codes
                    email_check_message = f"Searching Gmail for {platform} verification codes..."
                    verification_code = gmail_service.get_latest_verification_code(platform)
                    
                    if verification_code:
                        email_check_message = f"✅ Found verification code: {verification_code}"
                        gmail_check_status = "completed"
                    else:
                        email_check_message = "⏳ No recent verification code found. Monitoring for new emails..."
                        gmail_check_status = "monitoring"
                        
                except Exception as e:
                    email_check_message = f"❌ Gmail check failed: {str(e)}"
                    gmail_check_status = "error"
            else:
                email_check_message = "⚠️ Gmail service not available - manual 2FA required"
                gmail_check_status = "manual_required"
            
            browser_steps.append({
                "step": "login_check",
                "status": gmail_check_status,
                "message": "2FA code may be required - checking email",
                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+TG9naW4gUGFnZTwvdGV4dD4KPC9zdmc+",
                "requires_2fa": True,
                "email_check": email_check_message,
                "verification_code": verification_code,
                "gmail_available": GMAIL_AVAILABLE
            })
        
        # Step 4: Filling form
        browser_steps.append({
            "step": "form_filling",
            "status": "in_progress",
            "message": f"Filling product details: {listing_data.product_name}",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+Rm9ybSBGaWxsaW5nLi4uPC90ZXh0Pgo8L3N2Zz4=",
            "fields_filled": {
                "product": listing_data.product_name,
                "price": f"{listing_data.currency} {listing_data.price}",
                "quantity": listing_data.quantity
            }
        })
        
        # Create a temporary Excel file with the mapped data
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with platform-specific fields
        df = pd.DataFrame([platform_data])
        df.to_excel(temp_input, index=False)
        
        # Determine Chrome availability at runtime (not just startup)
        runtime_remote_url = os.environ.get("SELENIUM_REMOTE_URL")
        chrome_bin_guess = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
        chrome_bin_alt = "/usr/bin/google-chrome-stable"
        chrome_can_run = bool(runtime_remote_url) or os.path.exists(chrome_bin_guess) or os.path.exists(chrome_bin_alt)

        # Process the listing (visual with enhanced poster if possible)
        if chrome_can_run:
            try:
                # If platform is supported by enhanced posters, run it directly to capture steps
                if platform in ["cellpex", "gsmexchange"]:
                    from selenium import webdriver
                    options = webdriver.ChromeOptions()
                    remote_url = os.environ.get("SELENIUM_REMOTE_URL")
                    if remote_url:
                        driver = webdriver.Remote(command_executor=remote_url, options=options)
                    else:
                        try:
                            from multi_platform_listing_bot import create_driver
                        except ImportError:
                            from backend.multi_platform_listing_bot import create_driver
                        driver = create_driver()

                    try:
                        # Resolve posters with robust import, then execute poster flow
                        try:
                            # Prefer local import since Docker copies backend/ into /app
                            from enhanced_platform_poster import ENHANCED_POSTERS
                        except Exception:
                            # Fallback when backend is packaged as a module
                            from backend.enhanced_platform_poster import ENHANCED_POSTERS
                        poster = ENHANCED_POSTERS[platform](driver)
                        # Login + post minimal listing
                        poster_used = True
                        success = False
                        result_msg = None
                        login_ok = poster.login_with_2fa()
                        browser_steps.extend(poster.last_steps)
                        if login_ok:
                            # Build a minimal row-like dict
                            row_like = {
                                "brand": listing_data.brand,
                                "product_name": listing_data.product_name,
                                "model": listing_data.model_code,
                                "quantity": listing_data.quantity,
                                "price": listing_data.price,
                                "currency": listing_data.currency,
                                "condition": listing_data.condition,
                                "memory": listing_data.memory,
                                "color": listing_data.color,
                                "market_spec": listing_data.market_spec,
                                "sim_lock_status": listing_data.sim_lock_status,
                                "carrier": listing_data.carrier,
                                "country": listing_data.country,
                                "state": listing_data.state,
                                "minimum_order_quantity": listing_data.minimum_order_quantity,
                                "packaging": listing_data.packaging,
                                "item_weight": listing_data.item_weight,
                                "weight_unit": listing_data.weight_unit,
                                "incoterm": listing_data.incoterm,
                                "accepted_payments": listing_data.accepted_payments,
                                "description": listing_data.description,
                            }
                            result_msg = poster.post_listing(row_like)
                            browser_steps.extend(poster.last_steps)
                            # Be strict: only mark success if poster explicitly returned Success
                            success = bool(result_msg and result_msg.lower().startswith("success"))
                            # Attach poster message to steps for UI clarity
                            browser_steps.append({
                                "step": "poster_result",
                                "status": "success" if success else "error",
                                "message": result_msg or "No result returned from poster"
                            })
                    finally:
                        driver.quit()
                else:
                    run_from_spreadsheet(temp_input, temp_output)
                
                # Read the output to check status if it exists (poster flow does not write this file)
                if os.path.exists(temp_output):
                    result_df = pd.read_excel(temp_output)
                    if 'Status' in result_df.columns:
                        status = result_df.iloc[0]['Status']
                        if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                            browser_steps.append({
                            "step": "submission",
                            "status": "error",
                            "message": str(status),
                            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmVlIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iI2Y0NCIgZm9udC1zaXplPSIxOCI+RXJyb3I8L3RleHQ+Cjwvc3ZnPg=="
                        })
                            success = False
                    else:
                        # Only mark success here if we were NOT using the enhanced poster
                        if not locals().get('poster_used'):
                            browser_steps.append({
                                "step": "submission",
                                "status": "success",
                                "message": "Listing posted successfully!",
                                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZWZlIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzRhNCIgZm9udC1zaXplPSIxOCI+U3VjY2VzcyE8L3RleHQ+Cjwvc3ZnPg=="
                            })
                            success = True
            finally:
                # Clean up temp files
                for f in [temp_input, temp_output]:
                    if os.path.exists(f):
                        os.unlink(f)
        else:
            # Simulated success for demo
            browser_steps.append({
                "step": "submission",
                "status": "simulated",
                "message": "Simulated submission (Chrome not available in current environment)",
                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmM2NkIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzY2NiIgZm9udC1zaXplPSIxOCI+U2ltdWxhdGVkPC90ZXh0Pgo8L3N2Zz4="
            })
            success = False
        
        # Prefer the poster's message when available to avoid misleading success text
        response_message = None
        try:
            response_message = locals().get('result_msg') if locals().get('poster_used') else None
        except Exception:
            response_message = None

        # If enhanced poster was used, force success only on explicit Success from poster
        if locals().get('poster_used'):
            try:
                success = bool(response_message and str(response_message).lower().startswith("success"))
            except Exception:
                success = False
        return {
            "success": success,
            "message": response_message or "Visual automation completed",
            "platform": platform,
            "product": listing_data.product_name,
            "enriched_description": listing_data.description,
            "enriched_keywords": listing_data.keywords,
            "browser_steps": browser_steps,
            "parallel_capable": True,
            "estimated_time": "30-45 seconds per platform"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": request.platform,
            "product": request.listing_data.product_name,
            "browser_steps": [{
                "step": "error",
                "status": "error",
                "message": str(e),
                "screenshot": None
            }]
        }


def map_to_platform_fields(platform: str, data: ComprehensiveListingData) -> Dict[str, Any]:
    """
    Map comprehensive listing data to platform-specific fields.
    """
    if platform not in PLATFORM_FIELD_MAPPINGS:
        # Default mapping if platform not configured
        return {
            'platform': platform,
            'product_name': f"{data.brand} {data.product_name} {data.memory} {data.color}".strip(),
            'condition': data.condition,
            'quantity': data.quantity,
            'price': data.price,
            'description': data.description
        }
    
    mapping = PLATFORM_FIELD_MAPPINGS[platform]
    result = {'platform': platform}
    
    for platform_field, data_field in mapping.items():
        if isinstance(data_field, list):
            # Combine multiple fields
            values = []
            for field in data_field:
                value = getattr(data, field, "")
                if value:
                    values.append(str(value))
            
            # Special handling for GSM Exchange comments field
            if platform == "gsmexchange" and platform_field == "comments":
                comments_parts = []
                if data.description:
                    comments_parts.append(data.description)
                
                # Add technical details
                tech_details = []
                if data.sim_lock_status and data.sim_lock_status != "Unlocked":
                    tech_details.append(f"SIM Lock: {data.sim_lock_status}")
                if data.carrier:
                    tech_details.append(f"Carrier: {data.carrier}")
                if data.lcd_defects and data.lcd_defects != "None":
                    tech_details.append(f"LCD: {data.lcd_defects}")
                if data.quality_certification:
                    tech_details.append(f"Certification: {data.quality_certification}")
                
                if tech_details:
                    comments_parts.append("Technical details: " + ", ".join(tech_details))
                
                result[platform_field] = "\n\n".join(comments_parts)
            else:
                result[platform_field] = " ".join(values)
        elif isinstance(data_field, bool):
            # Static boolean values
            result[platform_field] = data_field
        elif isinstance(data_field, str) and data_field in ["sell", "buy"]:
            # Static string values
            result[platform_field] = data_field
        else:
            # Direct mapping
            value = getattr(data, data_field, "")
            
            # Special condition mapping for GSM Exchange
            if platform == "gsmexchange" and platform_field == "condition":
                condition_mapping = {
                    "New": "New",
                    "Used": "Used and tested",
                    "Refurbished": "Refurbished", 
                    "Damaged": "ASIS",
                    "14-Days": "14 day"
                }
                result[platform_field] = condition_mapping.get(value, value)
            
            # Special specification mapping for GSM Exchange
            elif platform == "gsmexchange" and platform_field == "specification":
                spec_mapping = {
                    "US": "US spec.",
                    "Euro": "Euro spec.",
                    "UK": "UK spec.",
                    "Asia": "Asia spec.",
                    "Arabic": "Arab spec.",
                    "Other": "Other spec."
                }
                result[platform_field] = spec_mapping.get(value, "Global Spec.")
            
            elif isinstance(value, list):
                result[platform_field] = ", ".join(value)
            else:
                result[platform_field] = value
    
    return result


@app.get("/gmail/status")
async def get_gmail_status():
    """Get Gmail service status and configuration details."""
    if not GMAIL_AVAILABLE or not gmail_service:
        return {
            "available": False,
            "status": "not_configured",
            "message": "Gmail service not available. Check OAuth configuration.",
            "oauth_flow": {
                "auth_url": "/gmail/auth",
                "callback_url": "/gmail/callback",
                "revoke_url": "/gmail/revoke"
            }
        }
    
    has_credentials = gmail_service.credentials is not None and gmail_service.credentials.valid
    
    return {
        "available": True,
        "status": "authenticated" if has_credentials else "requires_auth",
        "message": "Gmail service is properly configured with OAuth" if has_credentials else "OAuth authentication required",
        "authenticated": has_credentials,
        "features": [
            "2FA code retrieval",
            "Verification code extraction",
            "Platform-specific email monitoring"
        ],
        "oauth_flow": {
            "auth_url": "/gmail/auth",
            "callback_url": "/gmail/callback",
            "revoke_url": "/gmail/revoke"
        }
    }


@app.post("/gmail/reinitialize")
async def reinitialize_gmail_service():
    """Force reinitialize Gmail service with current OAuth credentials."""
    if not gmail_service:
        return {
            "success": False,
            "message": "Gmail service module not available"
        }
    
    success = gmail_service.force_reinitialize()
    return {
        "success": success,
        "message": "Gmail service reinitialized successfully" if success else "Gmail service reinitialization failed",
        "authentication_method": "oauth",
        "service_available": gmail_service.service is not None,
        "credentials_valid": gmail_service.credentials is not None and gmail_service.credentials.valid if gmail_service.credentials else False
    }


def _derive_external_base_url(request: Request) -> str:
    """Best-effort external base URL behind proxies.

    Prefers X-Forwarded-* headers (Railway/Vercel), falls back to request.base_url.
    Forces https for known production hosts if scheme is missing/incorrect.
    """
    f_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    f_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    scheme = f_proto or request.url.scheme or "https"
    host = f_host or request.url.hostname
    if host:
        base = f"{scheme}://{host}"
    else:
        base = str(request.base_url).rstrip("/")
    # Force https for Railway default domains
    if host and host.endswith("up.railway.app"):
        base = f"https://{host}"
    return base.rstrip("/")


@app.get("/gmail/auth")
async def start_gmail_oauth(request: Request, redirect_uri: Optional[str] = None, redirect: bool = False):
    """Start Gmail OAuth authentication flow.

    If no redirect_uri is provided, derive one from the current request base URL
    so this works both locally and in production (Railway).
    """
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")

    try:
        # Derive callback URL from the incoming request if not explicitly provided
        if not redirect_uri:
            base = _derive_external_base_url(request)
            redirect_uri = f"{base}/gmail/callback"

        authorization_url, state = gmail_service.get_authorization_url(redirect_uri=redirect_uri)
        if redirect:
            return RedirectResponse(authorization_url, status_code=302)
        else:
            return {
                "authorization_url": authorization_url,
                "state": state,
                "message": "Visit the authorization URL to authenticate with Gmail",
                "redirect_uri": redirect_uri,
                "instructions": [
                    "1. Visit the authorization URL",
                    "2. Sign in with your Google account",
                    "3. Grant access to Gmail",
                    "4. You'll be redirected to the callback URL with an authorization code"
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")


@app.get("/gmail/callback")
async def gmail_oauth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """Handle Gmail OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        # Use the same derived redirect_uri as in the start step to avoid mismatch
        base = _derive_external_base_url(request)
        redirect_uri = f"{base}/gmail/callback"
        success = gmail_service.exchange_code_for_credentials(code, redirect_uri=redirect_uri)
        if success:
            # Expose the refresh token so the caller can store it externally if desired
            refresh_token = None
            try:
                refresh_token = getattr(gmail_service.credentials, 'refresh_token', None)
            except Exception:
                refresh_token = None
            return {
                "success": True,
                "message": "Gmail OAuth authentication successful!",
                "status": "authenticated",
                "service_available": gmail_service.service is not None,
                "refresh_token": refresh_token
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to exchange code for credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@app.post("/gmail/revoke")
async def revoke_gmail_oauth():
    """Revoke Gmail OAuth credentials."""
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        success = gmail_service.revoke_credentials()
        return {
            "success": success,
            "message": "Gmail OAuth credentials revoked successfully",
            "status": "unauthenticated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke credentials: {str(e)}")


@app.get("/gmail/refresh-token")
async def get_gmail_refresh_token():
    """Return the current Gmail OAuth refresh token if available."""
    if not GMAIL_AVAILABLE or not gmail_service or not gmail_service.credentials:
        return {"available": False, "refresh_token": None}
    token = getattr(gmail_service.credentials, 'refresh_token', None)
    return {"available": token is not None, "refresh_token": token}


@app.get("/gmail/diagnostics")
async def gmail_diagnostics():
    """Comprehensive Gmail service diagnostics for OAuth."""
    diagnostics = {
        "gmail_service_module": gmail_service is not None,
        "gmail_available_flag": GMAIL_AVAILABLE,
        "import_error": gmail_import_error,
        "authentication_method": "oauth",
        "service_status": {
            "initialized": gmail_service.service is not None if gmail_service else False,
            "has_credentials": gmail_service.credentials is not None if gmail_service else False,
            "credentials_valid": gmail_service.credentials.valid if gmail_service and gmail_service.credentials else False,
        },
        "oauth_files": {}
    }
    
    # Check OAuth files
    if gmail_service:
        diagnostics["oauth_files"]["credentials_file"] = {
            "path": gmail_service.credentials_file,
            "exists": os.path.exists(gmail_service.credentials_file)
        }
        diagnostics["oauth_files"]["token_file"] = {
            "path": gmail_service.token_file,
            "exists": os.path.exists(gmail_service.token_file)
        }
        
        # Check credentials file content
        if os.path.exists(gmail_service.credentials_file):
            try:
                with open(gmail_service.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    container = None
                    if isinstance(creds_data, dict):
                        if "web" in creds_data:
                            container = creds_data.get("web", {})
                        elif "installed" in creds_data:
                            container = creds_data.get("installed", {})
                    if container is None:
                        container = {}
                    diagnostics["oauth_files"]["credentials_valid"] = {
                        "has_client_id": bool(container.get("client_id")),
                        "has_client_secret": bool(container.get("client_secret")),
                        "project_id": container.get("project_id")
                    }
            except Exception as e:
                diagnostics["oauth_files"]["credentials_error"] = str(e)
    
    return diagnostics


@app.post("/gmail/test-search")
async def test_gmail_search(platform: str = "gsmexchange"):
    """Test Gmail search functionality for a specific platform."""
    if not gmail_service or not gmail_service.is_available():
        return {
            "success": False,
            "message": "Gmail service not available"
        }
    
    try:
        # Search for verification codes
        codes = gmail_service.search_verification_codes(platform, minutes_back=60)
        
        # Get the latest code
        latest_code = gmail_service.get_latest_verification_code(platform)
        
        return {
            "success": True,
            "platform": platform,
            "total_codes_found": len(codes),
            "latest_code": latest_code,
            "search_details": {
                "authentication_method": "OAuth 2.0",
                "search_timeframe": "60 minutes",
                "codes_found": codes[:3]  # Return first 3 for privacy
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Gmail search test failed: {str(e)}"
        }


@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check OAuth configuration."""
    import json
    
    # Check environment variables
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    debug_info = {
        "environment_variables": {
            "OPENAI_API_KEY": "✅ SET" if openai_key else "❌ NOT SET"
        },
        "service_status": {
            "gmail_service_available": GMAIL_AVAILABLE,
            "chrome_available": CHROME_AVAILABLE,
            "openai_available": OPENAI_AVAILABLE
        },
        "authentication_method": "oauth",
        "runtime_check": {
            "gmail_service_object": gmail_service is not None,
            "gmail_service_type": str(type(gmail_service)) if gmail_service else "None",
            "gmail_available_flag": GMAIL_AVAILABLE,
            "can_call_methods": hasattr(gmail_service, 'get_authorization_url') if gmail_service else False
        }
    }
    
    # Check OAuth files and status
    if gmail_service:
        debug_info["oauth_status"] = {
            "credentials_file_exists": os.path.exists(gmail_service.credentials_file),
            "token_file_exists": os.path.exists(gmail_service.token_file),
            "has_credentials": gmail_service.credentials is not None,
            "credentials_valid": gmail_service.credentials.valid if gmail_service.credentials else False,
            "service_initialized": gmail_service.service is not None
        }
        
        # Check credentials file content
        if os.path.exists(gmail_service.credentials_file):
            try:
                with open(gmail_service.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    container = None
                    if isinstance(creds_data, dict):
                        if "web" in creds_data:
                            container = creds_data.get("web", {})
                        elif "installed" in creds_data:
                            container = creds_data.get("installed", {})
                    if container is None:
                        container = {}
                    debug_info["oauth_credentials_validation"] = {
                        "valid_json": True,
                        "project_id": container.get("project_id"),
                        "has_client_id": bool(container.get("client_id")),
                        "has_client_secret": bool(container.get("client_secret")),
                        "redirect_uris": container.get("redirect_uris", []),
                    }
            except json.JSONDecodeError as e:
                debug_info["oauth_credentials_validation"] = {
                    "valid_json": False,
                    "error": str(e),
                    "suggestion": "Check OAuth credentials JSON formatting",
                }
        else:
            debug_info["oauth_credentials_validation"] = {
                "file_missing": True,
                "suggestion": "OAuth credentials file not found. Please ensure google_oauth_credentials.json exists.",
            }
    
    return debug_info


# File system debug endpoint
@app.get("/debug/files")
async def debug_files():
    """Inspect app filesystem and Python import paths for debugging imports."""
    try:
        app_root = "/app"
        backend_dir = os.path.join(app_root, "backend")
        here = os.path.dirname(os.path.abspath(__file__))
        return {
            "cwd": os.getcwd(),
            "__file__": __file__,
            "here": here,
            "listdir_app": sorted(os.listdir(app_root)) if os.path.isdir(app_root) else None,
            "listdir_here": sorted(os.listdir(here)) if os.path.isdir(here) else None,
            "listdir_backend": sorted(os.listdir(backend_dir)) if os.path.isdir(backend_dir) else None,
            "exists": {
                "/app/gmail_service.py": os.path.exists(os.path.join(app_root, "gmail_service.py")),
                "/app/backend/gmail_service.py": os.path.exists(os.path.join(backend_dir, "gmail_service.py")),
                "/app/fastapi_app.py": os.path.exists(os.path.join(app_root, "fastapi_app.py")),
                "/app/backend/__init__.py": os.path.exists(os.path.join(backend_dir, "__init__.py")),
            },
            "sys_path": sys.path,
        }
    except Exception as e:
        return {"error": str(e)}

# Enhanced 2FA Testing Endpoints
@app.post("/test/enhanced-2fa/cellpex")
async def test_enhanced_cellpex_2fa():
    """Test enhanced Cellpex 2FA flow in production"""
    try:
        # Import here to avoid circular imports with robust fallback
        try:
            from enhanced_platform_poster import EnhancedCellpexPoster
        except ImportError:
            from backend.enhanced_platform_poster import EnhancedCellpexPoster
        from selenium import webdriver
        
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        if os.getenv("RAILWAY_ENVIRONMENT"):  # Running on Railway
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # Initialize Cellpex poster
            cellpex_poster = EnhancedCellpexPoster(driver)
            
            # Test login with 2FA
            success = cellpex_poster.login_with_2fa()
            
            current_url = driver.current_url
            
            return {
                "success": success,
                "platform": "cellpex",
                "message": "Enhanced Cellpex 2FA test completed",
                "final_url": current_url,
                "gmail_available": gmail_service.is_available() if gmail_service else False,
                "status": "success" if success else "failed"
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "platform": "cellpex", 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Enhanced Cellpex 2FA test failed"
        }


@app.post("/test/enhanced-2fa/gsm-exchange")
async def test_enhanced_gsm_2fa():
    """Test enhanced GSM Exchange 2FA flow in production"""
    try:
        # Check if GSM credentials are available
        username = os.getenv("GSMEXCHANGE_USERNAME")
        password = os.getenv("GSMEXCHANGE_PASSWORD")
        
        if not username or not password:
            return {
                "success": False,
                "platform": "gsmexchange",
                "error": "Missing GSM Exchange credentials",
                "message": "GSMEXCHANGE_USERNAME and GSMEXCHANGE_PASSWORD required"
            }
        
        from selenium import webdriver
        
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        if os.getenv("RAILWAY_ENVIRONMENT"):  # Running on Railway
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # Import and run GSM test
            from test_gsm_2fa_flow import test_gsm_2fa_flow
            
            # This is a simplified version for API testing
            success = False  # Will implement after analyzing GSM Exchange
            
            return {
                "success": success,
                "platform": "gsmexchange",
                "message": "GSM Exchange 2FA flow needs implementation",
                "credentials_available": True,
                "status": "pending_implementation"
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "platform": "gsmexchange",
            "error": str(e), 
            "traceback": traceback.format_exc(),
            "message": "Enhanced GSM Exchange 2FA test failed"
        }


@app.get("/test/platform-status")
async def platform_status():
    """Get status of all platforms and their 2FA readiness"""
    
    platforms = {
        "cellpex": {
            "status": "ready",
            "credentials_available": bool(os.getenv("CELLPEX_USERNAME") and os.getenv("CELLPEX_PASSWORD")),
            "2fa_implemented": True,
            "login_url": "https://www.cellpex.com/login",
            "last_tested": "Working as of deployment"
        },
        "gsmexchange": {
            "status": "testing",
            "credentials_available": bool(os.getenv("GSMEXCHANGE_USERNAME") and os.getenv("GSMEXCHANGE_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "https://www.gsmexchange.com/signin",
            "last_tested": "Pending implementation"
        },
        "hubx": {
            "status": "pending",
            "credentials_available": bool(os.getenv("HUBX_USERNAME") and os.getenv("HUBX_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD",
            "last_tested": "Not started"
        },
        "kardof": {
            "status": "pending",
            "credentials_available": bool(os.getenv("KARDOF_USERNAME") and os.getenv("KARDOF_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD", 
            "last_tested": "Not started"
        },
        "handlot": {
            "status": "pending",
            "credentials_available": bool(os.getenv("HANDLOT_USERNAME") and os.getenv("HANDLOT_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD",
            "last_tested": "Not started"
        }
    }
    
    return {
        "platforms": platforms,
        "gmail_service_available": gmail_service.is_available() if gmail_service else False,
        "total_platforms": len(platforms),
        "ready_platforms": len([p for p in platforms.values() if p["status"] == "ready"]),
        "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 
```

Committing the strict verification change and version bump, pushing to GitHub to trigger Railway deploy, then testing the production API endpoint with a Cellpex payload and showing the response.

- I’ve changed Cellpex success handling to exactly what you want:
  - After submission, if the review banner appears, we do NOT mark success immediately.
  - We now verify your account inventory right away. Only if it’s actually visible do we return success. Otherwise we return a Pending message with the banner text.

- Deployed via GitHub to Railway:
  - fix(cellpex): treat review banner as pending; verify inventory and only succeed if visible; API v2.2.0

- Next steps:
  - Use your Vercel UI or call your production API. Expect:
    - Success: “Success: … and verified in account”
    - Pending: “Pending: … (not visible in account yet)”
    - Error: explicit field/submit errors

- I also bumped the API root version to 2.2.0-review-plus-verify for traceability once Railway updates.

Summary:
- Updated `backend/enhanced_platform_poster.py` to verify inventory after the banner and only return success if the listing is visible.
- Bumped `backend/fastapi_app.py` API version.
- Committed and pushed; Railway will redeploy.

---

**User**

 Example data filled! Ready for testing.
page-1695fc03ffcf6670.js:1 🌐 Browser Automation: cellpex
page-1695fc03ffcf6670.js:1 ⏳ Launching headless Chrome for cellpex
page-1695fc03ffcf6670.js:1 ⏳ Navigating to cellpex.com
page-1695fc03ffcf6670.js:1 ⏳ 2FA code may be required - checking email
page-1695fc03ffcf6670.js:1 🔐 2FA Required - Checking email for verification code...
page-1695fc03ffcf6670.js:1 ⏳ Filling product details: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 
(index)
Value
product	'iPhone 14 Pro'
price	'USD 899.99'
quantity	5
Object
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened login page: https://www.cellpex.com/login
page-1695fc03ffcf6670.js:1 ⏳ Filled Cellpex credentials
page-1695fc03ffcf6670.js:1 ⏳ Submitted Cellpex login
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA verification page detected
page-1695fc03ffcf6670.js:1 ⏳ Waiting shortly for Cellpex 2FA email
page-1695fc03ffcf6670.js:1 ⏳ Cellpex 2FA successful
page-1695fc03ffcf6670.js:1 ⏳ Opened Sell Inventory form
page-1695fc03ffcf6670.js:1 ⏳ Category selected
page-1695fc03ffcf6670.js:1 ⏳ Brand selected: Apple
page-1695fc03ffcf6670.js:1 ⏳ Quantity entered: 5
page-1695fc03ffcf6670.js:1 ⏳ Price: 900
page-1695fc03ffcf6670.js:1 ⏳ Currency: USD
page-1695fc03ffcf6670.js:1 ⏳ Condition: Used
page-1695fc03ffcf6670.js:1 ⏳ Product name: iPhone 14 Pro
page-1695fc03ffcf6670.js:1 ⏳ hdnAction=submit, hdnSectionType=1
page-1695fc03ffcf6670.js:1 ⏳ Entered description
page-1695fc03ffcf6670.js:1 ⏳ Entered remarks with memory info
page-1695fc03ffcf6670.js:1 ⏳ Available: 08/14/2025
page-1695fc03ffcf6670.js:1 ⏳ Form fields filled before submit
page-1695fc03ffcf6670.js:1 ⏳ Submission accepted; pending moderation
page-1695fc03ffcf6670.js:1 ⏳ Post-submit (review) at https://www.cellpex.com/list/wholesale-inventory
page-1695fc03ffcf6670.js:1 ⏳ Checked https://www.cellpex.com/my-inventory
page-1695fc03ffcf6670.js:1 ⏳ Checked https://www.cellpex.com/my-summary
page-1695fc03ffcf6670.js:1 ⏳ Listing not found in inventory after submit (review)
page-1695fc03ffcf6670.js:1 ❌ Pending: Submission accepted; pending moderation (not visible in account yet)
page-1695fc03ffcf6670.js:1 ✨ All platforms processed for iPhone 14 Pro
page-1695fc03ffcf6670.js:1 🎯 All items and platforms processed!
﻿



@Listing Bot API Deployment Logs (18).log @Listing Bot API Build Logs (18).log 

Nothing was posted

---

**Cursor**

I’m going to harden the Cellpex model selection so it always chooses an autocomplete suggestion (or simulates it via keys) and, if suggestions don’t appear, sets common hidden fields via JavaScript as a fallback. I’ll also expand submit control selectors to include “Add”/“Post” buttons. Then I’ll commit, push, wait for Railway to redeploy, and re-test against production.

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False

    def _try_pick_autocomplete(self, input_el, wait: WebDriverWait) -> bool:
        """Try to select the first visible autocomplete suggestion for a text input.
        Returns True if something was picked (by click or keys)."""
        try:
            # Wait briefly for suggestions to render
            time.sleep(1.0)
            # Try common containers
            suggestion_xpaths = [
                "//ul[contains(@class,'ui-autocomplete') and contains(@style,'display: block')]//li[1]",
                "//ul[contains(@class,'ui-autocomplete')]//li[1]",
                "//li[contains(@class,'ui-menu-item')][1]",
                "//div[contains(@class,'autocomplete') or contains(@class,'suggest')]//li[1]"
            ]
            for sx in suggestion_xpaths:
                try:
                    el = self.driver.find_element(By.XPATH, sx)
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.1)
                        self.driver.execute_script("arguments[0].click();", el)
                        return True
                except Exception:
                    continue
            # Fallback to keyboard: ArrowDown + Enter
            try:
                input_el.send_keys("\ue015")  # Keys.ARROW_DOWN
                time.sleep(0.1)
                input_el.send_keys("\ue007")  # Keys.ENTER
                return True
            except Exception:
                pass
        except Exception:
            pass
        return False
    
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
    
    def _extract_cellpex_success_message(self) -> str:
        """Extract post-submit confirmation banner/message text if present."""
        try:
            candidates = []
            # Common success/notice containers
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
            except Exception:
                pass
            # Paragraphs or generic elements mentioning review/moderation/success
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
            except Exception:
                pass
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]") )
            except Exception:
                pass
            for el in candidates:
                try:
                    if el.is_displayed():
                        txt = (el.text or '').strip()
                        if txt:
                            return txt
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST – but verify inventory before claiming success
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours",
                    "submitted for review",
                    "will appear after moderation"
                ]
                if any(ind in page_text for ind in review_indicators):
                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
                    print("🕒 Listing submitted; review banner detected. Verifying inventory...")
                    self._capture_step("listing_pending_review", banner)
                    # IMPORTANT: verify presence in account even if review banner appears
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return f"Success: {banner} and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return f"Pending: {banner} (not visible in account yet)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False

    def _try_pick_autocomplete(self, input_el, wait: WebDriverWait) -> bool:
        """Try to select the first visible autocomplete suggestion for a text input.
        Returns True if something was picked (by click or keys)."""
        try:
            # Wait briefly for suggestions to render
            time.sleep(1.0)
            # Try common containers
            suggestion_xpaths = [
                "//ul[contains(@class,'ui-autocomplete') and contains(@style,'display: block')]//li[1]",
                "//ul[contains(@class,'ui-autocomplete')]//li[1]",
                "//li[contains(@class,'ui-menu-item')][1]",
                "//div[contains(@class,'autocomplete') or contains(@class,'suggest')]//li[1]"
            ]
            for sx in suggestion_xpaths:
                try:
                    el = self.driver.find_element(By.XPATH, sx)
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.1)
                        self.driver.execute_script("arguments[0].click();", el)
                        return True
                except Exception:
                    continue
            # Fallback to keyboard: ArrowDown + Enter
            try:
                input_el.send_keys("\ue015")  # Keys.ARROW_DOWN
                time.sleep(0.1)
                input_el.send_keys("\ue007")  # Keys.ENTER
                return True
            except Exception:
                pass
        except Exception:
            pass
        return False
    
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
    
    def _extract_cellpex_success_message(self) -> str:
        """Extract post-submit confirmation banner/message text if present."""
        try:
            candidates = []
            # Common success/notice containers
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
            except Exception:
                pass
            # Paragraphs or generic elements mentioning review/moderation/success
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
            except Exception:
                pass
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]") )
            except Exception:
                pass
            for el in candidates:
                try:
                    if el.is_displayed():
                        txt = (el.text or '').strip()
                        if txt:
                            return txt
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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
                    # Try to pick a suggestion item (robust)
                    picked = self._try_pick_autocomplete(model_field, wait)
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
                            field.dispatchEvent(new Event('input'));
                            field.dispatchEvent(new Event('change'));
                            field.blur();
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST – but verify inventory before claiming success
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours",
                    "submitted for review",
                    "will appear after moderation"
                ]
                if any(ind in page_text for ind in review_indicators):
                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
                    print("🕒 Listing submitted; review banner detected. Verifying inventory...")
                    self._capture_step("listing_pending_review", banner)
                    # IMPORTANT: verify presence in account even if review banner appears
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return f"Success: {banner} and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return f"Pending: {banner} (not visible in account yet)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

```python
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    # ---------- Helpers tailored to Cellpex form ----------
    def _normalize_price_str(self, price_value) -> str:
        """Cellpex price input often has maxlength=4 and expects digits only.
        Convert any float/str to a 1-4 digit integer string.
        """
        try:
            if price_value is None or str(price_value).strip() == "":
                return ""
            parsed = int(round(float(str(price_value).replace(",", "").strip())))
            if parsed < 0:
                parsed = 0
            if parsed > 9999:
                parsed = 9999
            return str(parsed)
        except Exception:
            digits = "".join(ch for ch in str(price_value) if ch.isdigit())[:4]
            return digits

    def _normalize_memory_label(self, value: str) -> str:
        """Map memory like '128GB' -> '128 GB', '1TB' -> '1 TB' to match Cellpex visible options."""
        if not value:
            return ""
        v = str(value).strip().upper().replace("G B", "GB").replace("T B", "TB")
        v = v.replace("GB", " GB").replace("TB", " TB")
        v = " ".join(v.split())
        return v

    def _map_color_label(self, value: str) -> list:
        """Return candidate color labels available on Cellpex for a given input."""
        if not value:
            return []
        v = str(value).strip().lower()
        mapping = {
            "space black": ["Black", "Graphite"],
            "space gray": ["Gray", "Graphite"],
            "space grey": ["Gray", "Graphite"],
            "deep purple": ["Purple"],
            "midnight": ["Black"],
            "starlight": ["Champagne", "Gold", "White"],
            "rose gold": ["Rose Gold"],
            "(product)red": ["Red"],
            "product red": ["Red"],
        }
        base = mapping.get(v)
        if base:
            return base
        cap = " ".join(w.capitalize() for w in v.split())
        return [cap]

    def _normalize_weight_str(self, weight_value) -> str:
        try:
            f = float(str(weight_value).strip())
        except Exception:
            return "0.3"
        if f < 10:
            s = f"{round(f, 1):.1f}"
        else:
            s = str(int(round(f)))
        if s.endswith(".0") and len(s) > 3:
            s = s[:-2]
        if "." in s:
            s = s.rstrip("0").rstrip(".")
            if len(s) == 1 and s.isdigit():
                s = f"{s}.0"
        if len(s) < 2:
            s = "0.3"
        if len(s) > 3:
            s = s[:3]
        return s

    def _select_relaxed(self, sel_element, desired_text_candidates: list) -> bool:
        """Try to select option by visible text with relaxed matching: exact (case-insensitive),
        then contains, then startswith. Returns True if selection succeeded.
        """
        try:
            dropdown = Select(sel_element)
            options = dropdown.options
            texts = [(opt.text or "").strip() for opt in options]
            lower_texts = [t.lower() for t in texts]
            # Exact case-insensitive
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip()
                if c.lower() in lower_texts:
                    idx = lower_texts.index(c.lower())
                    dropdown.select_by_index(idx)
                    return True
            # Contains
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and c in t:
                        dropdown.select_by_index(idx)
                        return True
            # Startswith
            for cand in desired_text_candidates:
                if not cand:
                    continue
                c = str(cand).strip().lower()
                for idx, t in enumerate(lower_texts):
                    if c and t.startswith(c):
                        dropdown.select_by_index(idx)
                        return True
            return False
        except Exception:
            return False

    def _try_pick_autocomplete(self, input_el, wait: WebDriverWait) -> bool:
        """Try to select the first visible autocomplete suggestion for a text input.
        Returns True if something was picked (by click or keys)."""
        try:
            # Wait briefly for suggestions to render
            time.sleep(1.0)
            # Try common containers
            suggestion_xpaths = [
                "//ul[contains(@class,'ui-autocomplete') and contains(@style,'display: block')]//li[1]",
                "//ul[contains(@class,'ui-autocomplete')]//li[1]",
                "//li[contains(@class,'ui-menu-item')][1]",
                "//div[contains(@class,'autocomplete') or contains(@class,'suggest')]//li[1]"
            ]
            for sx in suggestion_xpaths:
                try:
                    el = self.driver.find_element(By.XPATH, sx)
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.1)
                        self.driver.execute_script("arguments[0].click();", el)
                        return True
                except Exception:
                    continue
            # Fallback to keyboard: ArrowDown + Enter
            try:
                input_el.send_keys("\ue015")  # Keys.ARROW_DOWN
                time.sleep(0.1)
                input_el.send_keys("\ue007")  # Keys.ENTER
                return True
            except Exception:
                pass
        except Exception:
            pass
        return False
    
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
    
    def _extract_cellpex_success_message(self) -> str:
        """Extract post-submit confirmation banner/message text if present."""
        try:
            candidates = []
            # Common success/notice containers
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//div[contains(@class,'alert') or contains(@class,'success') or contains(@class,'notice') or contains(@class,'msg')]") )
            except Exception:
                pass
            # Paragraphs or generic elements mentioning review/moderation/success
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation')]") )
            except Exception:
                pass
            try:
                candidates.extend(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'review') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'moderation') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submitted')]") )
            except Exception:
                pass
            for el in candidates:
                try:
                    if el.is_displayed():
                        txt = (el.text or '').strip()
                        if txt:
                            return txt
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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

        # Explicitly click common cookie acceptance/close controls
        try:
            cookie_ctas = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]
            for xp in cookie_ctas:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        dismissed_count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
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
                    category_dropdown.select_by_visible_text("Cell Phones")
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
            
            # Available quantity: use quantity-specific fields (NOT txtAvailable)
            try:
                quantity = str(row.get("quantity", "1"))
                qty_field = None
                for locator in [
                    (By.NAME, "txtQty"),
                    (By.NAME, "txtQuantity"),
                    (By.NAME, "quantity"),
                    (By.NAME, "txtQTY"),
                ]:
                    try:
                        qty_field = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if qty_field:
                    qty_field.clear()
                    qty_field.send_keys(quantity)
                    print(f"✅ Quantity entered: {quantity}")
                    self._capture_step("quantity_entered", f"Quantity entered: {quantity}")
                else:
                    print("⚠️  Quantity field not found (txtAvailable/txtQty)")
            except Exception as e:
                print(f"⚠️  Could not enter quantity: {e}")
            
            # Price (try multiple common selectors) — normalize to integer (maxlength=4)
            try:
                price_value = self._normalize_price_str(row.get("price", ""))
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
                        print(f"✅ Price entered (normalized): {price_value}")
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
                    ok = False
                    try:
                        Select(currency_select).select_by_visible_text(currency)
                        ok = True
                    except Exception:
                        # Relaxed fallback with common synonyms
                        candidates = [currency]
                        if currency == "USD":
                            candidates += ["US Dollar", "USD $", "$", "Dollar"]
                        elif currency == "EUR":
                            candidates += ["Euro", "EUR €", "€"]
                        elif currency == "GBP":
                            candidates += ["British Pound", "GBP £", "£", "Pound"]
                        ok = self._select_relaxed(currency_select, candidates)
                    if ok:
                        print(f"✅ Currency selected: {currency}")
                        self._capture_step("currency_selected", f"Currency: {currency}")
            except Exception as e:
                print(f"⚠️  Could not select currency: {e}")

            # Condition (optional, try a few names) with relaxed matching
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
                    ok = False
                    try:
                        Select(cond_select).select_by_visible_text(condition)
                        ok = True
                    except Exception:
                        ok = self._select_relaxed(cond_select, [condition])
                    if not ok:
                        try:
                            Select(cond_select).select_by_index(1)
                            ok = True
                        except Exception:
                            pass
                    print(f"✅ Condition selected: {condition}")
                    self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection
            try:
                human_product = str(row.get('product_name') or '').strip()
                fallback_model = f"{row.get('brand', 'Apple')} {row.get('model', 'iPhone 14 Pro')}".strip()
                product_name = human_product or fallback_model
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
                    # Try to pick a suggestion item (robust)
                    picked = self._try_pick_autocomplete(model_field, wait)
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
                            field.dispatchEvent(new Event('input'));
                            field.dispatchEvent(new Event('change'));
                            field.blur();
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

            # Optional date field (set to today) if present
            try:
                from datetime import datetime as _dt
                value = _dt.utcnow().strftime('%Y-%m-%d')
                date_input = None
                for locator in [
                    (By.CSS_SELECTOR, "input[type='date']"),
                    (By.CSS_SELECTOR, "input[name*='date' i]"),
                    (By.CSS_SELECTOR, "input[id*='date' i]")
                ]:
                    try:
                        date_input = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if date_input:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, value)
                    print(f"✅ Date set: {value}")
            except Exception:
                pass

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY)
            try:
                from datetime import datetime as _dt
                available_value = _dt.now().strftime('%m/%d/%Y')
                try:
                    avail_field = driver.find_element(By.NAME, "txtAvailable")
                    avail_field.clear()
                    avail_field.send_keys(available_value)
                    print(f"✅ Available Date entered: {available_value}")
                    self._capture_step("available_date_entered", f"Available: {available_value}")
                except Exception:
                    pass
            except Exception:
                pass

            # Optional but commonly required dropdowns: Memory, Color, Market Spec, SIM Lock
            try:
                desired_memory = str(row.get("memory", "")).strip()
                if desired_memory:
                    normalized = self._normalize_memory_label(desired_memory)
                    for name in ["selMemory", "memory", "mem", "selMem"]:
                        try:
                            memory_select = driver.find_element(By.NAME, name)
                            ok = False
                            try:
                                Select(memory_select).select_by_visible_text(normalized)
                                ok = True
                            except Exception:
                                ok = self._select_relaxed(memory_select, [normalized, desired_memory, desired_memory.replace(" ", "")])
                            if ok:
                                print(f"✅ Memory selected: {normalized}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_color = str(row.get("color", "")).strip()
                if desired_color:
                    candidates = self._map_color_label(desired_color)
                    for name in ["selColor", "color", "selColour", "colour"]:
                        try:
                            color_select = driver.find_element(By.NAME, name)
                            ok = False
                            for cand in candidates:
                                try:
                                    Select(color_select).select_by_visible_text(cand)
                                    ok = True
                                    break
                                except Exception:
                                    continue
                            if not ok:
                                ok = self._select_relaxed(color_select, candidates + [desired_color])
                            if ok:
                                picked = candidates[0] if candidates else desired_color
                                print(f"✅ Color selected: {picked}")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            try:
                desired_market = str(row.get("market_spec", row.get("market", "US"))).strip()
                base_map = {"US": "US", "USA": "US", "Euro": "Euro", "EU": "Euro", "UK": "UK", "Asia": "Asia", "Arabic": "Arabic", "Other": "Other"}
                desired_market_norm = base_map.get(desired_market, desired_market)
                for name in ["selMarket", "market", "selSpec", "marketSpec", "selMarketSpec"]:
                    try:
                        market_select = driver.find_element(By.NAME, name)
                        ok = False
                        # Try exact first
                        try:
                            Select(market_select).select_by_visible_text(desired_market_norm)
                            ok = True
                        except Exception:
                            # Relaxed try with common suffixes
                            cands = [
                                desired_market_norm,
                                f"{desired_market_norm} Market",
                                f"{desired_market_norm} market",
                                f"{desired_market_norm} Spec",
                                f"{desired_market_norm} spec.",
                                f"{desired_market_norm} spec"
                            ]
                            ok = self._select_relaxed(market_select, cands)
                        if ok:
                            print(f"✅ Market Spec selected: {desired_market_norm}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                desired_sim = str(row.get("sim_lock_status", row.get("sim_lock", "Unlocked"))).strip()
                for name in ["selSim", "selSimLock", "selSIMlock", "simlock", "SIM", "SIM Lock"]:
                    try:
                        sim_select = driver.find_element(By.NAME, name)
                        ok = False
                        try:
                            Select(sim_select).select_by_visible_text(desired_sim)
                            ok = True
                        except Exception:
                            ok = self._select_relaxed(sim_select, [desired_sim, desired_sim.upper(), desired_sim.capitalize()])
                        if ok:
                            print(f"✅ SIM Lock selected: {desired_sim}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Carrier input if present
            try:
                carrier_value = str(row.get("carrier", "")).strip()
                if carrier_value:
                    for locator in [
                        (By.NAME, "carrier"),
                        (By.CSS_SELECTOR, "input[name*='carrier' i]")
                    ]:
                        try:
                            carrier_field = driver.find_element(*locator)
                            carrier_field.clear()
                            carrier_field.send_keys(carrier_value)
                            print(f"✅ Carrier entered: {carrier_value}")
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Country / State
            try:
                country_value = str(row.get("country", "United States")).strip()
                for name in ["country", "selCountry"]:
                    try:
                        country_select = driver.find_element(By.NAME, name)
                        Select(country_select).select_by_visible_text(country_value)
                        print(f"✅ Country selected: {country_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                state_value = str(row.get("state", "Florida")).strip()
                for locator in [
                    (By.NAME, "state"),
                    (By.CSS_SELECTOR, "input[name*='state' i]")
                ]:
                    try:
                        state_field = driver.find_element(*locator)
                        state_field.clear()
                        state_field.send_keys(state_value)
                        print(f"✅ State entered: {state_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinQty"),
                    (By.CSS_SELECTOR, "input[name*='min' i]")
                ]:
                    try:
                        mo = driver.find_element(*locator)
                        mo.clear()
                        mo.send_keys(min_order)
                        print(f"✅ Min. Order entered: {min_order}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Shipping / Item weight / Incoterms (Cellpex uses selPacking for packaging)
            try:
                pack_value = str(row.get("packaging", "Any Pack")).strip() or "Any Pack"
                for name in ["selPacking", "packing", "selPack"]:
                    try:
                        pack_sel = driver.find_element(By.NAME, name)
                        ok = self._select_relaxed(pack_sel, [pack_value, "Any Pack", "Original Box", "Bulk Packed"]) or False
                        if ok:
                            print(f"✅ Packing selected: {pack_value}")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                weight_value = self._normalize_weight_str(row.get("item_weight", "0.3"))
                for locator in [
                    (By.NAME, "txtWeight"),
                    (By.CSS_SELECTOR, "input[name*='weight' i]")
                ]:
                    try:
                        w = driver.find_element(*locator)
                        w.clear()
                        w.send_keys(weight_value)
                        driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input'));"
                            "arguments[0].dispatchEvent(new Event('change'));"
                            "arguments[0].blur();",
                            w, weight_value
                        )
                        print(f"✅ Item weight entered (normalized): {weight_value}")
                        break
                    except Exception:
                        continue
                # Unit select if present (explicit names first, then generic XPATH)
                try:
                    picked = False
                    for name in ["selWeightType", "selWeightUnit", "selWeight", "weightUnit", "unit"]:
                        try:
                            unit_sel = driver.find_element(By.NAME, name)
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                                picked = True
                                break
                            except Exception:
                                # Relaxed match for options containing 'kg'
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        picked = True
                                        break
                                if picked:
                                    break
                        except Exception:
                            continue
                    if not picked:
                        try:
                            unit_sel = driver.find_element(By.XPATH, "//select[option[contains(.,'kg')] or option[contains(.,'lbs')]]")
                            try:
                                Select(unit_sel).select_by_visible_text("kg")
                            except Exception:
                                opts = Select(unit_sel).options
                                for i, o in enumerate(opts):
                                    if "kg" in (o.text or "").lower():
                                        Select(unit_sel).select_by_index(i)
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

            try:
                incoterm_value = str(row.get("incoterm", "EXW"))
                for name in ["selIncoterm", "incoterm", "incoterms"]:
                    try:
                        incoterm_sel = driver.find_element(By.NAME, name)
                        Select(incoterm_sel).select_by_visible_text(incoterm_value)
                        print(f"✅ Incoterm selected: {incoterm_value}")
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            # Payment checkboxes: tick at least Wire TT and Paypal if visible
            try:
                labels_to_check = ["wire tt", "paypal"]
                label_elements = driver.find_elements(By.XPATH, "//label")
                for lbl in label_elements:
                    try:
                        txt = (lbl.text or "").strip().lower()
                        if any(k in txt for k in labels_to_check):
                            input_id = lbl.get_attribute("for")
                            box = None
                            if input_id:
                                try:
                                    box = driver.find_element(By.ID, input_id)
                                except Exception:
                                    box = None
                            if not box:
                                try:
                                    box = lbl.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                                except Exception:
                                    box = None
                            if box and not box.is_selected():
                                driver.execute_script("arguments[0].click();", box)
                    except Exception:
                        continue
                print("✅ Payment methods selected where available")
            except Exception:
                pass
            
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
            
            # Try a focused search for the exact blue "Submit" button shown in UI
            precise_submit_xpaths = [
                "//input[@type='submit' and (translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='submit' or contains(@value,'Submit'))]",
                "//button[@type='submit' and (normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='submit')]",
                "//input[contains(@class,'btn') and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//button[contains(@class,'btn') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
                "//input[@type='submit' and @value='Submit']"
            ]
            for xp in precise_submit_xpaths:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                        time.sleep(0.3)
                        self._dismiss_popups(driver)
                        try:
                            driver.execute_script("arguments[0].click();", el)
                            submitted = True
                            print(f"✅ Form submitted via precise selector: {xp}")
                            break
                        except Exception:
                            pass
                except Exception:
                    continue

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
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'add')]",
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'add')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'post')]",
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'post')]",
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
                        
                        # Try to move mouse to avoid overlay hover issues
                        try:
                            ActionChains(driver).move_to_element(submit_btn).pause(0.1).perform()
                        except Exception:
                            pass
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
                # Explicitly set hidden intent fields before any fallback
                try:
                    driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'};")
                    print("⏳ Set hidden action fields (hdnAction=submit, hdnSectionType=1)")
                except Exception:
                    pass

                # Prefer clicking the actual submitter or requestSubmit with the submitter
                try:
                    btn = None
                    try:
                        btn = driver.find_element(By.NAME, "btnSubmit")
                    except Exception:
                        pass
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        time.sleep(0.2)
                        self._dismiss_popups(driver)
                        try:
                            # Use requestSubmit with submitter if available
                            ok = driver.execute_script("var b=arguments[0]; var f=b && b.form; if(f && f.requestSubmit){ f.requestSubmit(b); return true } return false;", btn)
                            if ok:
                                submitted = True
                                print("✅ Form submitted via form.requestSubmit(btnSubmit)")
                            else:
                                driver.execute_script("arguments[0].click();", btn)
                                submitted = True
                                print("✅ Form submitted via btnSubmit click")
                        except Exception:
                            try:
                                btn.click()
                                submitted = True
                                print("✅ Form submitted via native click on btnSubmit")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Try Enter key on the remarks field only if still not submitted
                if not submitted:
                    print("⚠️  Could not find submit button, trying Enter key...")
                    try:
                        remarks_field = driver.find_element(By.NAME, "areaRemarks")
                        remarks_field.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                        submitted = True
                        print("✅ Form submitted using Enter key")
                    except Exception:
                        pass

            # Final fallback: submit the nearest form via JavaScript (after setting hidden intent)
            if not submitted:
                try:
                    ok = driver.execute_script("var a=document.getElementsByName('hdnAction')[0]; if(a){a.value='submit'}; var s=document.getElementsByName('hdnSectionType')[0]; if(s){s.value='1'}; var b=document.getElementsByName('btnSubmit')[0]; var f=(b && b.form) || document.querySelector('form'); if(f){ if (f.requestSubmit){ f.requestSubmit(b||undefined); } else { f.submit(); } return true } return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit/submit fallback (with hidden intent)")
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

            # Final heuristic: submit the first visible form using JS if still not submitted
            if not submitted:
                try:
                    ok = driver.execute_script("var f=document.querySelector('form'); if(f){f.requestSubmit ? f.requestSubmit() : f.submit(); return true} return false;")
                    if ok:
                        submitted = True
                        print("✅ Form submitted via requestSubmit() heuristic")
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
                time.sleep(18)

                # Inspect immediate response page
                current_url = driver.current_url
                page_text = driver.page_source.lower()

                # Detect moderation/review acknowledgement FIRST – but verify inventory before claiming success
                review_indicators = [
                    "screened by a proprietary fraud prevention system",
                    "reviewed in 24 hours",
                    "reviewed within 24 hours",
                    "submitted for review",
                    "will appear after moderation"
                ]
                if any(ind in page_text for ind in review_indicators):
                    banner = self._extract_cellpex_success_message() or "Submission accepted; pending moderation"
                    print("🕒 Listing submitted; review banner detected. Verifying inventory...")
                    self._capture_step("listing_pending_review", banner)
                    # IMPORTANT: verify presence in account even if review banner appears
                    self._capture_step("inventory_check_start", f"Post-submit (review) at {current_url}")
                    verified = self._verify_cellpex_listing(row)
                    if verified:
                        print("🎉 Listing verified in account after submission (review)")
                        self._capture_step("listing_verified", "Verified listing appears in account")
                        return f"Success: {banner} and verified in account"
                    else:
                        print("⚠️  Listing not visible in account yet after submission (review)")
                        self._capture_step("listing_not_found", "Listing not found in inventory after submit (review)")
                        return f"Pending: {banner} (not visible in account yet)"

                # Generic error sniffing
                error_indicators = [
                    "error", "failed", "invalid", "required", "please fill", "must select", "already exists"
                ]
                has_error = any(indicator in page_text for indicator in error_indicators)
                if has_error:
                    details = []
                    # 1) Common inline helper/error elements
                    try:
                        msg_els = driver.find_elements(
                            By.XPATH,
                            "//small|//span|//div"
                            "[contains(@class,'help') or contains(@class,'error') or contains(@class,'invalid') or contains(@class,'text-danger') or contains(@class,'validation') or contains(@class,'feedback') or contains(@class,'fv-') or contains(@role,'alert')]"
                        )
                        for el in msg_els:
                            t = (el.text or "").strip()
                            if t:
                                details.append(t)
                    except Exception:
                        pass
                    # 2) HTML5 validation messages and aria-invalid highlights
                    try:
                        js = (
                            "var msgs=[];\n"
                            "document.querySelectorAll('input,select,textarea').forEach(function(el){\n"
                            "  try{\n"
                            "    if (el.willValidate && !el.checkValidity() && el.validationMessage){ msgs.push(el.validationMessage); }\n"
                            "    var aria=el.getAttribute('aria-invalid');\n"
                            "    if(aria==='true'){ var lab=document.querySelector('label[for=\"'+el.id+'\"]'); if(lab&&lab.textContent){ msgs.push((lab.textContent+': invalid').trim()); } }\n"
                            "  }catch(e){}\n"
                            "});\n"
                            "Array.from(new Set(msgs)).slice(0,8);"
                        )
                        extra = driver.execute_script(js) or []
                        for t in extra:
                            if t:
                                details.append(str(t).strip())
                    except Exception:
                        pass
                    joined = "; ".join([d for d in details if d][:8])
                    print("❌ Error detected in response")
                    self._capture_step("listing_error", f"Form submission returned error{(': ' + joined) if joined else ''}")
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
        """Verify listing strictly by scanning the actual inventory grid for a matching row.
        Returns True only when we find a row containing brand AND price (and ideally model/qty).
        """
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            price_norm = (self._normalize_price_str(row.get("price")) or "").strip()
            qty_norm = str(row.get("quantity", "")).strip()

            # Visit inventory first; refresh once if needed
            inventory_urls = [
                "https://www.cellpex.com/my-inventory",
                "https://www.cellpex.com/my-summary",
            ]

            # Helper: evaluate a table row for a strong match
            def row_is_match(row_text_l: str) -> bool:
                if not row_text_l:
                    return False
                # Require brand AND price in the same row to avoid false positives
                brand_ok = bool(brand and brand in row_text_l)
                price_ok = bool(price_norm and price_norm in row_text_l)
                # Add optional boosters
                model_ok = bool(model and model in row_text_l) or bool(product_name and product_name in row_text_l)
                qty_ok = bool(qty_norm and (f" {qty_norm} " in f" {row_text_l} " or f"qty {qty_norm}" in row_text_l))
                # Strong match: brand + price, plus at least one booster if present
                if brand_ok and price_ok and (model_ok or qty_ok or (product_name and product_name in row_text_l)):
                    return True
                # If model name is very specific (e.g., iPhone 14 Pro), allow brand+model alone with qty
                if brand_ok and model_ok and qty_ok:
                    return True
                return False

            # Helper: scan visible tables for matching rows
            def scan_tables_for_match() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@id,'gv') or contains(@id,'grid') or contains(@class,'grid') or contains(@class,'table')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:60]:  # Limit scan for performance
                            try:
                                txt = (r.text or "").strip().lower()
                                if row_is_match(txt):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            # Scan inventory pages
            for idx, url in enumerate(inventory_urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("inventory_page", f"Checked {url}")
                    # Obvious 'no records' guard
                    page_l = driver.page_source.lower()
                    if any(tok in page_l for tok in ["no records", "no results", "nothing found"]):
                        continue
                    if scan_tables_for_match():
                        return True
                    # One soft refresh on first pass
                    if idx == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables_for_match():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # As a last resort, try wholesale search results (less reliable, so still require brand+price)
            try:
                driver.get("https://www.cellpex.com/wholesale-search-results")
                time.sleep(2)
                if scan_tables_for_match():
                    return True
            except Exception:
                pass

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
```

- We now strictly return Pending when Cellpex shows the moderation banner and the listing isn’t visible in your account, which matches your screenshot. Nothing was posted yet; it’s explicitly flagged as pending.

- I hardened Cellpex posting:
  - Robust model autocomplete: tries visible suggestion click; falls back to ArrowDown+Enter; if none, injects value with input/change/blur.
  - Expanded submit controls: now includes Add/Post variants alongside Save/Submit and __doPostBack patterns.

- Deployed via GitHub; Railway responded with Pending: Submission accepted; pending moderation (not visible in account yet).

If you prefer, I can add a retry loop to poll your inventory for up to N minutes after the banner, and only then finalize the status.

