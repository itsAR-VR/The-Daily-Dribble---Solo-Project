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
            'gsmexchange': [
                'my account', 'post listing', 'dashboard',
                'phones', 'add offer', 'new offer', 'post offers'
            ],
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
    
    # -------- Anti-bot hardening helpers (stealth + human-like interaction) --------
    def _install_stealth(self) -> None:
        """Install basic stealth overrides via Chrome DevTools and pre-page scripts."""
        driver = self.driver
        try:
            # User agent + locale + timezone overrides
            try:
                driver.execute_cdp_cmd("Network.setUserAgentOverride", {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                })
            except Exception:
                pass
            try:
                driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": "en-US"})
            except Exception:
                pass
            try:
                driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/New_York"})
            except Exception:
                pass

            # Stealth script evaluated before document scripts
            stealth_script = """
                // Navigator.webdriver
                Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => undefined });
                // Languages
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                // Plugins
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                // Chrome runtime
                window.chrome = window.chrome || { runtime: {} };
                // WebGL vendor/renderer spoof
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter){
                  if (parameter === 37445) { return 'Intel Inc.'; } // UNMASKED_VENDOR_WEBGL
                  if (parameter === 37446) { return 'Intel Iris OpenGL Engine'; } // UNMASKED_RENDERER_WEBGL
                  return getParameter.call(this, parameter);
                };
            """
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script})
            except Exception:
                # Fallback: inject after load as well (less effective but harmless)
                try:
                    driver.execute_script(stealth_script)
                except Exception:
                    pass
        except Exception:
            pass

    def _human_pause(self, min_ms: int = 60, max_ms: int = 180) -> None:
        import random, time as _t
        try:
            _t.sleep(random.uniform(min_ms/1000.0, max_ms/1000.0))
        except Exception:
            pass

    def _human_wiggle_mouse(self, intensity: int = 3) -> None:
        """Small, human-like cursor movements to reduce static cursor signature."""
        try:
            from selenium.webdriver.common.action_chains import ActionChains as _AC
            import random
            ac = _AC(self.driver)
            for _ in range(intensity):
                try:
                    ac.move_by_offset(random.randint(-5, 5), random.randint(-3, 3)).pause(random.uniform(0.05, 0.15)).perform()
                except Exception:
                    break
        except Exception:
            pass

    def _human_click(self, element) -> bool:
        try:
            from selenium.webdriver.common.action_chains import ActionChains as _AC
            import random
            self._human_wiggle_mouse(2)
            ac = _AC(self.driver)
            try:
                ac.move_to_element(element).pause(random.uniform(0.1, 0.25)).perform()
                # jitter
                ac.move_by_offset(random.randint(-2, 2), random.randint(-2, 2)).pause(random.uniform(0.05, 0.15)).click().perform()
                return True
            except Exception:
                pass
            # Fallback: direct click
            try:
                element.click()
                return True
            except Exception:
                pass
            # Last resort: JS click
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def _human_type(self, element, text: str) -> None:
        import random, time as _t
        try:
            element.click()
        except Exception:
            try:
                self._human_click(element)
            except Exception:
                pass
        for ch in str(text):
            try:
                element.send_keys(ch)
            except Exception:
                # Small refocus attempt
                try:
                    element.click(); element.send_keys(ch)
                except Exception:
                    pass
            _t.sleep(random.uniform(0.04, 0.11))
            # Occasional micro-pause
            if random.random() < 0.08:
                _t.sleep(random.uniform(0.15, 0.35))

    def _bot_block_detected(self) -> bool:
        try:
            body_l = (self.driver.page_source or "").lower()
            markers = [
                "captcha", "are you human", "unusual activity", "bot", "access denied", "verify you are",
                "incapsula", "cloudflare", "ddos", "robot check"
            ]
            return any(m in body_l for m in markers)
        except Exception:
            return False

    def login_with_2fa(self) -> bool:
        """GSM Exchange specific login with optional email 2FA.
        Hardened with longer waits, cookie dismissal, CTA fallbacks, iframe scan and success heuristics.
        """
        driver = self.driver
        try:
            # Install stealth and human-like behavior before first navigation
            try:
                self._install_stealth()
            except Exception:
                pass
            self._human_wiggle_mouse(2)

            # Be generous with page load and element waits during login
            try:
                driver.set_page_load_timeout(60)
            except Exception:
                pass
            wait_short = WebDriverWait(driver, 15)
            wait_long = WebDriverWait(driver, 60)

            # Open login page and dismiss any blocking popups
            driver.get(self.LOGIN_URL)
            self._capture_step("gsmx_login_page", f"Opened login page: {self.LOGIN_URL}")
            try:
                self._dismiss_gsmx_popups()
            except Exception:
                pass

            if self._bot_block_detected():
                self._capture_step("gsmx_bot_block", "Captcha or bot-detection page detected at login")
                # Try a small wait and refresh once to allow human-like retry
                time.sleep(3)
                try:
                    driver.refresh(); time.sleep(2)
                    self._dismiss_gsmx_popups()
                except Exception:
                    pass

            # Sometimes the email/password form is hidden behind a CTA – try a few obvious ones
            for xp in [
                "//button[contains(.,'Sign in') or contains(.,'Log in') or contains(.,'Continue')]",
                "//a[contains(.,'Sign in') or contains(.,'Log in') or contains(.,'Continue')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]",
            ]:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        self._human_click(el)
                        time.sleep(1)
                        self._dismiss_gsmx_popups()
                except Exception:
                    continue

            # If the form is inside an iframe, try to switch to it
            def _try_switch_to_login_iframe() -> bool:
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                except Exception:
                    iframes = []
                for i, fr in enumerate(iframes[:6]):
                    try:
                        driver.switch_to.default_content()
                        driver.switch_to.frame(fr)
                        # Probe for username/email field quickly
                        if driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input#email, input#username"):
                            return True
                    except Exception:
                        continue
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
                return False

            _try_switch_to_login_iframe()

            # Locate username/email field with broad selector set
            user_field = None
            user_selectors = [
                (By.NAME, "email"), (By.ID, "email"), (By.CSS_SELECTOR, "input[type='email']"),
                (By.NAME, "username"), (By.ID, "username"),
                (By.CSS_SELECTOR, "input[autocomplete='username']"),
                (By.CSS_SELECTOR, "input[name*='login' i]"),
                (By.CSS_SELECTOR, "input[id*='login' i]"),
                (By.CSS_SELECTOR, "input[name*='user' i]"),
                (By.CSS_SELECTOR, "input[id*='user' i]"),
                (By.CSS_SELECTOR, "form input:not([type='hidden'])[type='text']"),
            ]
            for by, sel in user_selectors:
                try:
                    user_field = wait_long.until(EC.presence_of_element_located((by, sel)))
                    break
                except Exception:
                    continue
            if not user_field:
                # Try once more after clicking likely CTAs and switching frames again
                _try_switch_to_login_iframe()
                self._dismiss_gsmx_popups()
                for by, sel in user_selectors:
                    try:
                        user_field = wait_short.until(EC.presence_of_element_located((by, sel)))
                        break
                    except Exception:
                        continue
            if not user_field:
                raise TimeoutException("username/email input not found")
            try:
                user_field.clear()
            except Exception:
                pass
            self._human_type(user_field, self.username)

            # Locate password field with broad selector set
            pass_field = None
            pass_selectors = [
                (By.NAME, "password"), (By.ID, "password"), (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
                (By.CSS_SELECTOR, "input[name*='pass' i]"),
                (By.CSS_SELECTOR, "input[id*='pass' i]"),
            ]
            for by, sel in pass_selectors:
                try:
                    pass_field = wait_long.until(EC.presence_of_element_located((by, sel)))
                    break
                except Exception:
                    continue
            if not pass_field:
                raise TimeoutException("password input not found")
            try:
                pass_field.clear()
            except Exception:
                pass
            self._human_type(pass_field, self.password)
            self._capture_step("gsmx_login_filled", "Filled GSMX credentials")

            # Submit the form
            submitted = False
            for by, sel in [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(.,'Sign in') or contains(.,'Login') or contains(.,'Log in') or contains(.,'Continue')]")
            ]:
                try:
                    btn = driver.find_element(by, sel)
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                    time.sleep(0.2)
                    self._dismiss_gsmx_popups()
                    self._human_click(btn)
                    submitted = True
                    break
                except Exception:
                    continue
            if not submitted:
                try:
                    pass_field.send_keys("\n")
                    submitted = True
                except Exception:
                    pass
            self._capture_step("gsmx_login_submitted", "Submitted GSMX login")

            # Give time for redirect and check for 2FA prompt
            time.sleep(3)
            try:
                self._dismiss_gsmx_popups()
            except Exception:
                pass

            if self._bot_block_detected():
                self._capture_step("gsmx_bot_block", "Captcha or bot-detection screen after submit")
                # Wait a little and do a gentle refresh once
                time.sleep(3)
                try:
                    driver.refresh(); time.sleep(2)
                    self._dismiss_gsmx_popups()
                except Exception:
                    pass
            page_l = driver.page_source.lower()
            needs_2fa = any(k in page_l for k in [
                "verification", "verify your identity", "2fa", "enter code", "security code", "authentication code"
            ]) or bool(driver.find_elements(By.XPATH, "//input[@name='code' or @name='otp' or @name='token']"))
            if needs_2fa:
                self._capture_step("gsmx_2fa_page", "GSMX 2FA verification page detected")
                if not self._handle_gsmx_2fa():
                    return False

            # Heuristic success: URL no longer contains 'signin' and page has dashboard/account keywords
            try:
                WebDriverWait(driver, 20).until(lambda d: "signin" not in (d.current_url or "").lower())
            except Exception:
                pass
            if self._check_login_success():
                self._capture_step("gsmx_login_success", "Logged in to GSMX")
                return True

            # As a fallback, try alternative login routes once more if we still appear logged out
            for url in [
                "https://www.gsmexchange.com/login",
                "https://www.gsmexchange.com/en/login",
                "https://www.gsmexchange.com/en/signin",
                "https://www.gsmexchange.com/trading/signin",
            ]:
                try:
                    driver.get(url)
                    time.sleep(2)
                    self._dismiss_gsmx_popups()
                    # Quick probe for already-authenticated state
                    if self._check_login_success():
                        self._capture_step("gsmx_login_success", f"Logged in via fallback: {url}")
                        return True
                except Exception:
                    continue

            # Final state – capture debug and treat as timeout/failure
            try:
                dbg = driver.execute_script(
                    "return {url: location.href, title: document.title, hasForm: !!document.querySelector('form'), body: (document.body && document.body.innerText) ? document.body.innerText.slice(0,800) : ''}"
                )
            except Exception:
                dbg = None
            self._capture_step("gsmx_login_timeout", f"Login timeout{(' | ' + str(dbg)) if dbg else ''}")
            return False
        except TimeoutException:
            self._capture_step("gsmx_login_timeout", "Login timeout")
            return False
        except Exception as e:
            self._capture_step("gsmx_login_error", f"{e}")
            return False

    def _handle_gsmx_2fa(self) -> bool:
        """Enter the GSM Exchange verification code from Gmail."""
        if not self.gmail_service:
            print("❌ Gmail service not available for 2FA")
            return False
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        try:
            print("📧 Waiting for GSMX 2FA email…")
            time.sleep(10)
            # Search recent emails from gsmexchange
            code = None
            try:
                results = self.gmail_service.service.users().messages().list(
                    userId='me', q='from:gsmexchange.com newer_than:1d', maxResults=5
                ).execute()
                messages = results.get('messages', [])
                if messages:
                    msg_id = messages[0]['id']
                    msg = self.gmail_service.service.users().messages().get(userId='me', id=msg_id).execute()
                    snippet = msg.get('snippet', '')
                    import re
                    codes = re.findall(r"\b(\d{6})\b", snippet)
                    if codes:
                        code = codes[0]
            except Exception:
                pass
            if not code:
                # fallback to generic extractor
                recent = self._search_recent_emails("gsmexchange", minutes_back=10)
                if recent:
                    code = self._llm_extract_auth_code(recent[0].get('content',''), recent[0].get('subject',''))
            if not code:
                print("❌ No GSMX 2FA code found")
                return False
            # Enter code
            field = None
            for by, sel in [
                (By.NAME, 'code'), (By.ID, 'code'), (By.NAME, 'otp'), (By.NAME, 'token'),
                (By.CSS_SELECTOR, "input[type='text'][maxlength='6']")
            ]:
                try:
                    field = wait.until(EC.presence_of_element_located((by, sel)))
                    break
                except Exception:
                    continue
            if not field:
                print("❌ GSMX 2FA input not found")
                return False
            field.clear(); field.send_keys(code)
            # Submit
            for by, sel in [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(.,'Verify') or contains(.,'Submit') or contains(.,'Continue')]")
            ]:
                try:
                    btn = driver.find_element(by, sel)
                    driver.execute_script("arguments[0].click();", btn)
                    break
                except Exception:
                    continue
            time.sleep(2)
            return self._check_login_success()
        except Exception as e:
            print(f"❌ Error entering GSMX 2FA code: {e}")
            return False

    def _dismiss_gsmx_popups(self) -> None:
        """Dismiss common GSM Exchange popups/cookie banners that may block inputs."""
        driver = self.driver
        try:
            # Quick CSS-based accepts/close
            for by, sel in [
                (By.CSS_SELECTOR, "#onetrust-accept-btn-handler"),
                (By.CSS_SELECTOR, "button.cookie-accept"),
                (By.CSS_SELECTOR, "[class*='cookie'] button"),
                (By.CSS_SELECTOR, "button[aria-label='close']"),
                (By.CSS_SELECTOR, ".modal [data-dismiss='modal']"),
            ]:
                try:
                    el = driver.find_element(by, sel)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                except Exception:
                    continue
            # Text based (Accept/OK/Continue)
            for xp in [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
                "//button[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//a[contains(.,'OK') or contains(.,'Ok') or contains(.,'ok')]",
                "//button[contains(@class,'close') or contains(.,'×') or contains(.,'x')]",
            ]:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                except Exception:
                    continue
        except Exception:
            pass

    def _open_offer_form(self) -> bool:
        """Navigate to a working Add Offer form. Returns True if the model input is present."""
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        candidates = [
            "https://www.gsmexchange.com/en/phones",
            "https://www.gsmexchange.com/en/phones/add",
            "https://www.gsmexchange.com/en/trading/add-offer",
            "https://www.gsmexchange.com/trading/add-offer",
            "https://www.gsmexchange.com/gsm/post_offers.html",
        ]
        for url in candidates:
            try:
                driver.get(url)
                time.sleep(2)
                self._dismiss_gsmx_popups()
                for by, sel in [
                    (By.NAME, "phModelFull"),
                    (By.CSS_SELECTOR, "input[data-component='trading/phoneAutocompleter']"),
                    (By.CSS_SELECTOR, ".twitter-typeahead input.tt-query"),
                ]:
                    try:
                        wait.until(EC.presence_of_element_located((by, sel)))
                        self._capture_step("gsmx_offer_form", f"Offer form ready at {url}")
                        return True
                    except Exception:
                        continue
            except Exception:
                continue
        self._capture_step("gsmx_offer_form_missing", "Could not locate Add Offer form")
        return False

    def _read_inline_errors(self) -> str:
        """Collect visible inline validation and helper messages from the page."""
        driver = self.driver
        msgs = []
        try:
            nodes = driver.find_elements(By.XPATH, "//div|//span|//small|//p")
            for n in nodes:
                try:
                    t = (n.text or '').strip()
                    if not t:
                        continue
                    l = t.lower()
                    if any(k in l for k in ["required", "invalid", "error", "select", "please", "missing", "must"]):
                        msgs.append(t)
                except Exception:
                    continue
        except Exception:
            pass
        try:
            extra = driver.execute_script(
                "var m=[];document.querySelectorAll('input,select,textarea').forEach(function(el){try{if(el.willValidate&&!el.checkValidity()&&el.validationMessage){m.push(el.validationMessage)}}catch(e){}});return Array.from(new Set(m)).slice(0,6);"
            ) or []
            for t in extra:
                if t and t not in msgs:
                    msgs.append(t)
        except Exception:
            pass
        return "; ".join(msgs[:6])

    def _verify_gsmx_listing(self, row) -> bool:
        """Scan likely 'My offers' pages for a matching row (brand + price, with optional model)."""
        try:
            driver = self.driver
            brand = (str(row.get("brand", "")).strip() or "").lower()
            product_name = (str(row.get("product_name", "")).strip() or "").lower()
            model = (str(row.get("model", "")).strip() or "").lower()
            try:
                price = row.get("price")
                price_norm = str(int(round(float(str(price).replace(",", "").strip())))) if price is not None else ""
            except Exception:
                price_norm = "".join(ch for ch in str(row.get("price", "")) if ch.isdigit())

            def row_is_match(text_l: str) -> bool:
                if not text_l:
                    return False
                brand_ok = bool(brand and brand in text_l)
                price_ok = bool(price_norm and price_norm in text_l)
                model_ok = bool(model and model in text_l) or bool(product_name and product_name in text_l)
                if brand_ok and (price_ok or model_ok):
                    return True
                return False

            def scan_tables() -> bool:
                try:
                    tables = driver.find_elements(By.XPATH, "//table[contains(@class,'table') or contains(@class,'grid') or contains(@id,'offer')]")
                    for tbl in tables:
                        if not tbl.is_displayed():
                            continue
                        rows = tbl.find_elements(By.XPATH, ".//tr[td]")
                        for r in rows[:80]:
                            try:
                                t = (r.text or '').strip().lower()
                                if row_is_match(t):
                                    return True
                            except Exception:
                                continue
                    return False
                except Exception:
                    return False

            urls = [
                "https://www.gsmexchange.com/en/phones?tab=offers",
                "https://www.gsmexchange.com/en/trading/my-offers",
                "https://www.gsmexchange.com/trading/my-offers",
                "https://www.gsmexchange.com/gsm/my_offers.html",
            ]
            for i, url in enumerate(urls):
                try:
                    driver.get(url)
                    time.sleep(3)
                    self._capture_step("gsmx_verify", f"Checked {url}")
                    if scan_tables():
                        return True
                    if i == 0:
                        try:
                            driver.refresh(); time.sleep(2)
                            if scan_tables():
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def post_listing(self, row):
        """Post listing on GSM Exchange (Phones > Add offer → I want to sell)."""
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        
        def _try_pick_typeahead(input_el, text: str) -> bool:
            try:
                input_el.clear()
                for chunk in text.split(" "):
                    input_el.send_keys(chunk + " ")
                    time.sleep(0.2)
                time.sleep(1)
                # Try dropdown item
                try:
                    dropdown = driver.find_element(By.CSS_SELECTOR, ".tt-dropdown-menu")
                    if dropdown.is_displayed():
                        try:
                            first_item = dropdown.find_element(By.XPATH, ".//div|.//li")
                            driver.execute_script("arguments[0].click();", first_item)
                            return True
                        except Exception:
                            pass
                except Exception:
                    pass
                # Keyboard fallback
                try:
                    input_el.send_keys("\ue015")  # ArrowDown
                    time.sleep(0.1)
                    input_el.send_keys("\ue007")  # Enter
                    return True
                except Exception:
                    return False
            except Exception:
                return False

        try:
            # Navigate to phones page first (new UI), then fallback to legacy offers page
            driver.get("https://www.gsmexchange.com/en/phones")
            time.sleep(2)
            self._dismiss_gsmx_popups()
            self._capture_step("gsmx_phones", "Opened GSM Exchange phones page")
            # Ensure the add-offer form exists; otherwise navigate to legacy, or try robust fallbacks
            form_present = False
            try:
                driver.find_element(By.NAME, "phModelFull")
                form_present = True
            except Exception:
                form_present = False
            if not form_present:
                driver.get("https://www.gsmexchange.com/gsm/post_offers.html")
                time.sleep(2)
                self._dismiss_gsmx_popups()
                self._capture_step("gsmx_legacy", "Opened legacy post offers page")
                try:
                    driver.find_element(By.NAME, "phModelFull")
                    form_present = True
                except Exception:
                    form_present = False
            if not form_present:
                if not self._open_offer_form():
                    return "Error: Could not open GSM Exchange Add Offer form"

            # Pick SELL if radio is present
            try:
                sell_radio = driver.find_element(By.CSS_SELECTOR, "input[value='sell']")
                if sell_radio.is_displayed():
                    driver.execute_script("arguments[0].click();", sell_radio)
                    self._capture_step("gsmx_sell", "Selected I want to sell")
            except Exception:
                pass

            # Model autocomplete (phModelFull)
            product_name = str(row.get("product_name") or row.get("model") or row.get("model_code") or "").strip()
            if product_name:
                try:
                    # Support both new and legacy typeahead inputs
                    model_input = None
                    for by, sel in [
                        (By.NAME, "phModelFull"),
                        (By.CSS_SELECTOR, "input[data-component='trading/phoneAutocompleter']"),
                        (By.CSS_SELECTOR, ".twitter-typeahead input.tt-query"),
                    ]:
                        try:
                            model_input = wait.until(EC.presence_of_element_located((by, sel)))
                            break
                        except Exception:
                            continue
                    if not model_input:
                        raise TimeoutException("model input not found")
                    picked = _try_pick_typeahead(model_input, product_name)
                    self._capture_step("gsmx_model", f"Model set: {product_name}{' (picked)' if picked else ''}")
                except Exception:
                    pass

            # Quantity (phQty)
            try:
                qty_val = str(row.get("quantity", "1"))
                qty_el = None
                for loc in [(By.ID, "f-at-qty"), (By.NAME, "phQty")]:
                    try:
                        qty_el = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if qty_el:
                    qty_el.clear(); qty_el.send_keys(qty_val)
                    self._capture_step("gsmx_qty", f"Quantity: {qty_val}")
            except Exception:
                pass

            # Currency (phCurrency)
            try:
                currency = str(row.get("currency", "USD")).upper()
                cur_el = None
                for loc in [(By.ID, "f-at-currency"), (By.NAME, "phCurrency")]:
                    try:
                        cur_el = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if cur_el:
                    try:
                        Select(cur_el).select_by_value(currency)
                    except Exception:
                        Select(cur_el).select_by_visible_text(currency)
                    self._capture_step("gsmx_currency", f"Currency: {currency}")
            except Exception:
                pass

            # Price (phPrice)
            try:
                price_val = str(row.get("price", ""))
                price_el = None
                for loc in [(By.ID, "f-at-price"), (By.NAME, "phPrice")]:
                    try:
                        price_el = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if price_el:
                    price_el.clear(); price_el.send_keys(price_val)
                    self._capture_step("gsmx_price", f"Price: {price_val}")
            except Exception:
                pass

            # Condition (phCondition)
            try:
                cond = str(row.get("condition", "New")).strip()
                cond_map = {
                    "new": "New",
                    "used": "Used and tested",
                    "refurbished": "Refurbished",
                    "14-days": "7 day / 14 day",
                    "14 days": "7 day / 14 day",
                    "asis": "ASIS",
                    "cpo": "CPO",
                    "pre order": "Pre order",
                }
                desired = cond_map.get(cond.lower(), cond)
                cond_el = None
                for loc in [(By.ID, "f-at-condition"), (By.NAME, "phCondition")]:
                    try:
                        cond_el = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if cond_el:
                    ok = False
                    try:
                        Select(cond_el).select_by_visible_text(desired)
                        ok = True
                    except Exception:
                        # relaxed contains
                        options = Select(cond_el).options
                        for i, o in enumerate(options):
                            if desired.lower() in (o.text or "").lower():
                                Select(cond_el).select_by_index(i)
                                ok = True
                                break
                    if ok:
                        self._capture_step("gsmx_condition", f"Condition: {desired}")
            except Exception:
                pass

            # Specification (phSpec) from market_spec
            try:
                spec = str(row.get("market_spec", row.get("market", "US"))).strip().upper()
                spec_map = {
                    "US": "US spec.",
                    "EURO": "Euro spec.",
                    "EU": "Euro spec.",
                    "UK": "UK spec.",
                    "ASIA": "Asia spec.",
                    "ARABIC": "Arab spec.",
                    "ARAB": "Arab spec.",
                    "INDIA": "Indian spec.",
                    "INDIAN": "Indian spec.",
                    "AFRICA": "African spec.",
                    "LATIN": "Latin spec.",
                    "JAPAN": "Japanese spec.",
                    "JAPANESE": "Japanese spec.",
                    "CHINA": "China spec.",
                    "CANADA": "Canada Spec.",
                    "GLOBAL": "Global Spec.",
                    "OTHER": "Other spec.",
                }
                desired = spec_map.get(spec, "Global Spec.")
                spec_el = None
                for loc in [(By.ID, "f-at-spec"), (By.NAME, "phSpec")]:
                    try:
                        spec_el = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if spec_el:
                    ok = False
                    try:
                        Select(spec_el).select_by_visible_text(desired)
                        ok = True
                    except Exception:
                        options = Select(spec_el).options
                        for i, o in enumerate(options):
                            if desired.lower() in (o.text or "").lower():
                                Select(spec_el).select_by_index(i)
                                ok = True
                                break
                    if ok:
                        self._capture_step("gsmx_spec", f"Spec: {desired}")
            except Exception:
                pass

            # Comments (phComments)
            try:
                comments = row.get("description") or ""
                if not comments:
                    comments = f"Condition: {row.get('condition','')} | Memory: {row.get('memory','')} | Color: {row.get('color','')}"
                com_el = None
                for loc in [(By.ID, "comments"), (By.NAME, "phComments")]:
                    try:
                        com_el = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if com_el:
                    com_el.clear(); com_el.send_keys(comments[:1000])
                    self._capture_step("gsmx_comments", "Comments entered")
            except Exception:
                pass

            # Confirm physical stock (confirm)
            try:
                cb = None
                for loc in [(By.ID, "f-at-confirm"), (By.NAME, "confirm")]:
                    try:
                        cb = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if cb and not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    self._capture_step("gsmx_confirm", "Confirmed physical stock")
            except Exception:
                pass

            # Submit the offer (site-specific selectors for primary button)
            submitted = False
            for loc in [
                (By.CSS_SELECTOR, "button.primary.c-tOR-item[type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit'].primary"),
                (By.CSS_SELECTOR, "button.c-tOR-item[type='submit']"),
                (By.XPATH, "//button[@type='submit' and contains(.,'New offer') or contains(.,'Post') or contains(.,'Create') or contains(.,'Submit')]")
            ]:
                try:
                    btn = driver.find_element(*loc)
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", btn)
                    submitted = True
                    self._capture_step("gsmx_submit", "Clicked New offer")
                    break
                except Exception:
                    continue
            # Additional submit fallbacks (legacy forms)
            if not submitted:
                for by, sel in [
                    (By.CSS_SELECTOR, "input[type='submit'][value*='New offer' i]"),
                    (By.CSS_SELECTOR, "input[type='submit'][value*='Post' i]"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.CSS_SELECTOR, "input[type='submit']"),
                    (By.XPATH, "//input[@type='submit' and contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add offer')]")
                ]:
                    try:
                        btn = driver.find_element(by, sel)
                        driver.execute_script("arguments[0].click();", btn)
                        submitted = True
                        self._capture_step("gsmx_submit_fallback", f"Clicked submit via {sel}")
                        break
                    except Exception:
                        continue

            if not submitted:
                self._capture_step("gsmx_no_submit", "Submit button not found")
                return "Error: Could not submit GSM Exchange offer"

            # Wait for a success cue
            time.sleep(4)
            page = driver.page_source.lower()
            # Targeted success banner (site-specific)
            try:
                banner = driver.find_element(By.XPATH, "//div[contains(@class,'alert') and contains(@class,'success')] | //div[contains(@class,'notice') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success')] | //p[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'offer has been')]")
                if banner and banner.is_displayed():
                    txt = (banner.text or '').strip()
                    self._capture_step("gsmx_success_banner", txt)
                    return "Success: GSM Exchange offer posted"
            except Exception:
                pass
            # Generic success text
            if any(k in page for k in ["offer created", "new offer", "offer posted", "successfully", "thank you", "your offer", "offer has been"]):
                # Try to verify in My Offers for confirmation
                if self._verify_gsmx_listing(row):
                    return "Success: GSM Exchange offer posted and verified"
                return "Success: GSM Exchange offer posted"
            # Error sniffing with inline details
            if any(k in page for k in ["invalid", "required", "please", "error", "missing", "select model", "select a model"]):
                details = self._read_inline_errors()
                self._capture_step("gsmx_error", f"Form error: {details}")
                return "Error: Form submission failed - check required fields"
            # As a final step, try verifying in My Offers even without an explicit success banner
            if self._verify_gsmx_listing(row):
                return "Success: GSM Exchange offer posted (verified)"
            return "Pending: Submitted offer; waiting for confirmation"
            
        except TimeoutException:
            return "Timeout posting listing"
        except Exception as e:
            self._capture_step("gsmx_exception", str(e))
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

    def _try_pick_autocomplete(self, input_el, wait: WebDriverWait, desired_text: str | None = None) -> bool:
        """Try to select an autocomplete suggestion for a text input.
        Preference order: a suggestion matching desired_text, otherwise the first visible item.
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
            # If we know the desired text, look for any suggestion item that matches it
            if desired_text:
                try:
                    sug_items = self.driver.find_elements(By.XPATH, "//ul[contains(@class,'ui-autocomplete')]//li | //li[contains(@class,'ui-menu-item')] | //div[contains(@class,'autocomplete') or contains(@class,'suggest')]//li")
                    for it in sug_items:
                        try:
                            if it.is_displayed():
                                txt = (it.text or "").strip().lower()
                                if txt and all(t in txt for t in desired_text.lower().split()[:2]):
                                    self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", it)
                                    time.sleep(0.1)
                                    self.driver.execute_script("arguments[0].click();", it)
                                    return True
                        except Exception:
                            continue
                except Exception:
                    pass
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
            try:
                driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));", user_field)
            except Exception:
                pass
            
            pass_field = wait.until(EC.presence_of_element_located(
                (By.NAME, "txtPass")
            ))
            pass_field.clear()
            pass_field.send_keys(self.password)
            try:
                driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));", pass_field)
            except Exception:
                pass
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
            
            # Section selection: PHONES & TABLETS (1), ACCESSORIES (2), GADGETS (G)
            section_mode = 'phones_tablets'
            try:
                section_raw = str(row.get('section') or row.get('product_type') or row.get('category') or '').lower()
                desired_section = '1'
                if any(k in section_raw for k in ['accessor', 'accessories']):
                    desired_section = '2'
                elif any(k in section_raw for k in ['gadget', 'gadgets']):
                    desired_section = 'G'
                # Allow explicit override
                desired_section = str(row.get('selSection') or row.get('selSectionValue') or desired_section)
                radios = driver.find_elements(By.NAME, 'selSection')
                for r in radios:
                    try:
                        if (r.get_attribute('value') or '').upper() == desired_section.upper():
                            driver.execute_script("arguments[0].click();", r)
                            section_mode = 'accessories' if desired_section == '2' else ('gadgets' if desired_section.upper() == 'G' else 'phones_tablets')
                            self._capture_step('section_selected', f'Section {section_mode}')
                            time.sleep(0.6)  # let form switch
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            
            # Category selection (selCateg) — support Cell Packs and Accessories/Gadgets
            try:
                category_select = wait.until(EC.presence_of_element_located((By.NAME, "selCateg")))
                from selenium.webdriver.support.ui import Select
                requested_cat = str(row.get("category", "")).strip()
                product_type = str(row.get("product_type", "")).strip().lower()
                product_name_l = (str(row.get("product_name", "")).strip().lower())
                ok = False
                # 1) If caller provided a category, try that first (relaxed)
                if requested_cat:
                    ok = self._select_relaxed(category_select, [requested_cat])
                # 2) Heuristics by section
                if not ok:
                    if section_mode in ('accessories', 'gadgets'):
                        # No default; just pick first non-empty if nothing specified
                        ok = False
                    else:
                        # Phones & Tablets: prefer Cell Packs if indicated, else Cell Phones
                        wants_packs = (
                            ("pack" in requested_cat.lower()) or
                            ("pack" in product_type) or
                            ("pack" in product_name_l)
                        )
                        if wants_packs:
                            ok = self._select_relaxed(category_select, [
                                "Cell Packs", "Packs", "Cell Phone Packs", "Phone Packs"
                            ])
                        else:
                            ok = self._select_relaxed(category_select, [
                                "Cell Phones", "Cell Phones & Tablets", "Cell Phones / Tablets & Smartwatches"
                            ]) or ok
                # 3) Absolute fallback: first non-empty option
                if not ok:
                    try:
                        Select(category_select).select_by_index(1)
                        ok = True
                    except Exception:
                        pass
                if ok:
                    picked_label = requested_cat or ("(auto)" if section_mode in ('accessories','gadgets') else ("Cell Packs" if 'pack' in (requested_cat.lower() if requested_cat else '') else "Cell Phones"))
                    print("✅ Category selected")
                    self._capture_step("category_selected", f"Category selected: {picked_label}")
                else:
                    print("⚠️  Category not selected (no matching option)")
            except Exception as e:
                print(f"⚠️  Could not select category: {e}")

            # Ensure SELL/WTS is selected if a radio exists
            try:
                wts_radios = driver.find_elements(By.XPATH, "//input[@type='radio'][contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sell') or contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'wts')]")
                if wts_radios:
                    for r in wts_radios:
                        try:
                            if r.is_displayed():
                                driver.execute_script("arguments[0].click();", r)
                                print("✅ Selected Sell/WTS radio")
                                self._capture_step("sell_radio_selected", "WTS/Sell selected")
                                break
                        except Exception:
                            continue
            except Exception:
                pass
            
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
            
            # Accessories/Gadgets specific fields: txtCode, txtBrand (optional), txtModel
            if section_mode in ('accessories', 'gadgets'):
                # Name or code
                try:
                    code_value = str(row.get('code') or row.get('product_code') or row.get('product_name') or row.get('model') or '').strip()[:39]
                    if code_value:
                        code_el = None
                        for loc in [(By.ID, 'txtCode'), (By.NAME, 'txtCode')]:
                            try:
                                code_el = driver.find_element(*loc)
                                break
                            except Exception:
                                continue
                        if code_el:
                            code_el.clear()
                            code_el.send_keys(code_value)
                            print(f"✅ Name/Code entered: {code_value}")
                            self._capture_step('code_entered', f'Code/Name: {code_value}')
                except Exception:
                    pass
                # Optional brand text field
                try:
                    brand_text = str(row.get('brand', '')).strip()[:39]
                    if brand_text:
                        for loc in [(By.ID, 'txtBrand'), (By.NAME, 'txtBrand')]:
                            try:
                                b = driver.find_element(*loc)
                                b.clear(); b.send_keys(brand_text)
                                print("✅ Brand text entered")
                                break
                            except Exception:
                                continue
                except Exception:
                    pass
                # Model text field
                try:
                    model_text = str(row.get('model') or row.get('product_name') or '').strip()[:39]
                    if model_text:
                        for loc in [(By.ID, 'txtModel'), (By.NAME, 'txtModel')]:
                            try:
                                m = driver.find_element(*loc)
                                m.clear(); m.send_keys(model_text)
                                print("✅ Model entered")
                                self._capture_step('model_entered', f'Model: {model_text}')
                                break
                            except Exception:
                                continue
                except Exception:
                    pass
            
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
            
            # Price (try multiple common selectors) — normalize to integer respecting field maxlength
            try:
                raw_price = row.get("price", "")
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
                    try:
                        mx = price_field.get_attribute('maxlength')
                        max_len = int(mx) if (mx and str(mx).isdigit()) else 6
                    except Exception:
                        max_len = 6
                    try:
                        normalized_int = int(round(float(str(raw_price).replace(',', '').strip())))
                        digits = str(normalized_int)
                    except Exception:
                        digits = "".join(ch for ch in str(raw_price) if ch.isdigit())
                    if max_len > 0:
                        digits = digits[:max_len]
                    price_field.clear()
                    price_field.send_keys(digits)
                    print(f"✅ Price entered (normalized): {digits}")
                    self._capture_step("price_entered", f"Price: {digits}")
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

            # Condition for all sections: support select dropdown or radio group
            try:
                condition = str(row.get("condition", "Used")).strip()
                try:
                    radios = driver.find_elements(By.XPATH, "//input[@type='radio' and @name='selCondition']")
                except Exception:
                    radios = []
                if radios:
                    value_map = {"new": "1", "used": "2", "refurbished": "4", "damaged": "7", "14-days": "8", "14 days": "8"}
                    key = condition.lower()
                    val = value_map.get(key, None)
                    if val:
                        try:
                            el = driver.find_element(By.CSS_SELECTOR, f"input[type='radio'][name='selCondition'][value='{val}']")
                            if el.is_displayed():
                                driver.execute_script("arguments[0].click();", el)
                                print(f"✅ Condition selected (radio): {condition}")
                                self._capture_step("condition_selected", f"Condition: {condition}")
                        except Exception:
                            pass
                else:
                    cond_select = None
                    for name in ["selCondition", "selCond", "condition"]:
                        try:
                            el = driver.find_element(By.NAME, name)
                            if el.tag_name.lower() == 'select':
                                cond_select = el
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
                        if ok:
                            print(f"✅ Condition selected: {condition}")
                            self._capture_step("condition_selected", f"Condition: {condition}")
            except Exception as e:
                print(f"⚠️  Could not select condition: {e}")

            # Brand/Model description (txtBrandModel) with autocomplete selection (Phones & Tablets only)
            if section_mode == 'phones_tablets':
                try:
                    human_product = str(row.get('product_name') or '').strip()
                    brand_val = str(row.get('brand', '')).strip()
                    fallback_model = f"{brand_val or 'Apple'} {row.get('model', 'iPhone 14 Pro')}".strip()
                    if human_product and brand_val and brand_val.lower() not in human_product.lower():
                        product_name = f"{brand_val} {human_product}".strip()
                    else:
                        product_name = human_product or fallback_model
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
                        for chunk in product_name.split(" "):
                            model_field.send_keys(chunk + " ")
                            time.sleep(0.3)
                        time.sleep(1.5)
                        picked = self._try_pick_autocomplete(model_field, wait, product_name)
                        if not picked:
                            try:
                                hidden_ok = False
                                for hf in driver.find_elements(By.CSS_SELECTOR, "input[type='hidden']"):
                                    try:
                                        name = (hf.get_attribute('name') or hf.get_attribute('id') or '').lower()
                                        val = (hf.get_attribute('value') or '').strip()
                                        if name and val and any(tok in name for tok in ['modelid','brandid','itemid','hdnmodel','hdnbrand']):
                                            hidden_ok = True
                                    except Exception:
                                        continue
                                if not hidden_ok:
                                    model_field.send_keys("\ue015")
                                    time.sleep(0.1)
                                    model_field.send_keys("\ue007")
                                    picked = True
                            except Exception:
                                pass
                        if not picked:
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input')); arguments[0].dispatchEvent(new Event('change')); arguments[0].blur();", model_field, product_name)
                        print(f"✅ Product name set: {product_name} {'(picked suggestion)' if picked else '(direct)'}")
                        self._capture_step("product_name_set", f"Product name: {product_name}")
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
                        driver.execute_script("""
                            var field = document.querySelector('[name=\"txtBrandModel\"]');
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
            
            # Description: Phones use areaComments; Gadgets/Accessories use areaDesc
            try:
                description = str(row.get("description", f"High quality {row.get('brand', 'Apple')} device in {row.get('condition', 'excellent')} condition"))
                desc_el = None
                for locator in [
                    (By.NAME, "areaComments"), (By.ID, "areaComments"),
                    (By.NAME, "areaDesc"), (By.ID, "areaDesc"),
                    (By.CSS_SELECTOR, "textarea[name*='desc' i]"),
                ]:
                    try:
                        desc_el = driver.find_element(*locator)
                        break
                    except Exception:
                        continue
                if desc_el:
                    driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input')); arguments[0].dispatchEvent(new Event('change'));", desc_el, description)
                    print("✅ Description entered")
                self._capture_step("description_entered", "Entered description")
            except Exception as e:
                print(f"⚠️  Could not enter description: {e}")
            
            # Remarks (areaRemarks) - Enhanced with memory info, using JavaScript injection (phones only)
            try:
                remarks_field = wait.until(EC.presence_of_element_located((By.NAME, "areaRemarks")))
                remarks = f"Memory: {row.get('memory', '128GB')} | Condition: {row.get('condition', 'Excellent')} | Color: {row.get('color', 'Space Black')}"
                driver.execute_script("arguments[0].value = arguments[1];", remarks_field, remarks)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", remarks_field)
                print("✅ Remarks entered (JavaScript injection with memory info)")
                self._capture_step("remarks_entered", "Entered remarks with memory info")
            except Exception as e:
                print(f"⚠️  Could not enter remarks: {e}")

            # Keywords (Gadgets page requires txtKeywords)
            try:
                kw_items = row.get("keywords") or []
                if isinstance(kw_items, list):
                    kw_str = ", ".join([str(k) for k in kw_items if k])
                else:
                    kw_str = str(kw_items)
                if kw_str:
                    kw_el = None
                    for locator in [(By.ID, "txtKeywords"), (By.NAME, "txtKeywords")]:
                        try:
                            kw_el = driver.find_element(*locator)
                            break
                        except Exception:
                            continue
                    if kw_el:
                        kw_el.clear(); kw_el.send_keys(kw_str)
                        self._capture_step("keywords_entered", f"Keywords: {kw_str[:60]}")
                        print("✅ Keywords entered")
            except Exception:
                pass

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

            # Explicitly handle Cellpex Available Date text field (txtAvailable -> MM/DD/YYYY) with robust JS
            try:
                from datetime import datetime as _dt
                available_value = str(row.get('available_from') or _dt.now().strftime('%m/%d/%Y'))
                locators = [
                    (By.NAME, 'txtAvailable'), (By.ID, 'txtAvailable'),
                    (By.CSS_SELECTOR, "input[name*='Available' i]")
                ]
                set_ok = False
                for loc in locators:
                    try:
                        el = driver.find_element(*loc)
                        driver.execute_script(
                            "try{arguments[0].removeAttribute('readonly')}catch(e){};"
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));"
                            "arguments[0].blur();",
                            el, available_value
                        )
                        time.sleep(0.1)
                        set_ok = True
                        break
                    except Exception:
                        continue
                if set_ok:
                    print(f"✅ Available From set: {available_value}")
                    self._capture_step('available_date_entered', f"Available: {available_value}")
                else:
                    print("⚠️  Could not locate Available From input")
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
                desired_sim = (str(row.get('sim_lock_status') or row.get('sim_lock') or 'Unlocked')).strip() or 'Unlocked'
                sim_names = [
                    'selSim','selSIM','selSimLock','selSIMLock','selSimType','simlock','simLock','SELLOCK','SIM','SIM Lock'
                ]
                sim_select = None
                for nm in sim_names:
                    try:
                        sim_select = driver.find_element(By.NAME, nm)
                        break
                    except Exception:
                        continue
                if not sim_select:
                    try:
                        sim_select = driver.find_element(By.XPATH, "//select[option and (contains(.,'Unlocked') or contains(.,'Locked'))]")
                    except Exception:
                        sim_select = None
                if sim_select:
                    labels = [desired_sim, 'Factory Unlocked','Unlocked','SIM Free','Network Unlocked','Locked']
                    ok = False
                    for label in labels:
                        try:
                            Select(sim_select).select_by_visible_text(label)
                            ok = True
                            break
                        except Exception:
                            continue
                    if not ok:
                        ok = self._select_relaxed(sim_select, labels + [desired_sim.upper(), desired_sim.capitalize()])
                    if ok:
                        print(f"✅ SIM Lock selected: {desired_sim}")
                        self._capture_step('sim_lock_selected', desired_sim)
                    else:
                        print("⚠️  Could not select SIM lock option")
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
                    (By.NAME, "txtState"),
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

            # Allow local pickup checkbox
            try:
                desired_pickup = bool(row.get('allow_local_pickup', False))
                cb = None
                for loc in [
                    (By.NAME, 'chkLocalPickup'),
                    (By.ID, 'chkLocalPickup'),
                    (By.CSS_SELECTOR, "input[type='checkbox'][name*='pickup' i]")
                ]:
                    try:
                        cb = driver.find_element(*loc)
                        break
                    except Exception:
                        continue
                if cb:
                    if cb.is_selected() != desired_pickup:
                        driver.execute_script("arguments[0].click();", cb)
                    print(f"✅ Local pickup set: {desired_pickup}")
            except Exception:
                pass

            # Min. Order
            try:
                min_order = str(row.get("minimum_order_quantity", row.get("min_order", "1")))
                for locator in [
                    (By.NAME, "txtMin"),
                    (By.NAME, "txtMinOrder"),
                    (By.NAME, "txtMinimumOrder"),
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

            # Quality/Safety Certification (txtQuality)
            try:
                quality = str(row.get("quality_certification", "")).strip()
                if quality:
                    el = None
                    for loc in [(By.ID, "txtQuality"), (By.NAME, "txtQuality")]:
                        try:
                            el = driver.find_element(*loc)
                            break
                        except Exception:
                            continue
                    if el:
                        el.clear(); el.send_keys(quality)
                        print("✅ Quality/Certification entered")
            except Exception:
                pass

            # Delivery time (txtDelivery)
            try:
                delivery = str(row.get("delivery_days", "")).strip()
                if delivery:
                    el = None
                    for loc in [(By.ID, "txtDelivery"), (By.NAME, "txtDelivery")]:
                        try:
                            el = driver.find_element(*loc)
                            break
                        except Exception:
                            continue
                    if el:
                        el.clear(); el.send_keys(delivery)
                        print(f"✅ Delivery time entered: {delivery} days")
            except Exception:
                pass

            # Supply ability (txtSupplyAbility)
            try:
                supply = str(row.get("supply_ability", "")).strip()
                if supply:
                    el = None
                    for loc in [(By.ID, "txtSupplyAbility"), (By.NAME, "txtSupplyAbility")]:
                        try:
                            el = driver.find_element(*loc)
                            break
                        except Exception:
                            continue
                    if el:
                        el.clear(); el.send_keys(supply)
                        print(f"✅ Supply ability entered: {supply}")
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
                    # Enumerate candidate controls to discover real event targets (broaden signals)
                    candidates = driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button' or @type='image'] | //button | //a[@onclick]")
                    targets = []
                    for el in candidates:
                        try:
                            value_txt = el.get_attribute('value') or ''
                            visible_txt = el.text or ''
                            id_attr = el.get_attribute('id') or ''
                            name_attr = el.get_attribute('name') or ''
                            alt_attr = el.get_attribute('alt') or ''
                            title_attr = el.get_attribute('title') or ''
                            onclick = el.get_attribute('onclick') or ''
                            combined = " ".join([value_txt, visible_txt, id_attr, name_attr, alt_attr, title_attr]).lower()
                            blob = f"id={id_attr} name={name_attr} val={value_txt} txt={visible_txt} alt={alt_attr} title={title_attr}"
                            keywords = ["save", "post", "submit", "add", "publish", "send", "confirm"]
                            if any(k in combined for k in keywords):
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