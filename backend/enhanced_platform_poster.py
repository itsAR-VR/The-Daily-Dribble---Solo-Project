#!/usr/bin/env python3
"""
Enhanced platform poster with Gmail 2FA integration and optional step-by-step screenshot capture.
"""

import time
import base64
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
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

# Manual 2FA store (human fallback)
try:
    from manual_2fa_store import (
        wait_for_code as manual_2fa_wait,
        fetch_and_clear as manual_2fa_fetch_and_clear,
        prepare as manual_2fa_prepare,
        clear as manual_2fa_clear,
    )
except Exception:
    from .manual_2fa_store import (
        wait_for_code as manual_2fa_wait,
        fetch_and_clear as manual_2fa_fetch_and_clear,
        prepare as manual_2fa_prepare,
        clear as manual_2fa_clear,
    )

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
        # Adaptive pacing baseline (ms)
        self._pace_slow_ms = 200
        self._pace_fast_ms = 60
        self._last_action_ts = time.time()
        self.manual_job_id: Optional[str] = None

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
    
    # ---- Cookie/session helpers ----
    def _save_cookies(self, scope: str) -> None:
        try:
            cookies = self.driver.get_cookies()
            os.makedirs("/tmp/listing_cookies", exist_ok=True)
            path = f"/tmp/listing_cookies/{self.PLATFORM.lower()}_{scope}.json"
            import json
            with open(path, "w") as f:
                json.dump(cookies, f)
        except Exception:
            pass

    def _load_cookies(self, scope: str) -> bool:
        try:
            path = f"/tmp/listing_cookies/{self.PLATFORM.lower()}_{scope}.json"
            import json
            if not os.path.exists(path):
                return False
            with open(path, "r") as f:
                cookies = json.load(f)
            for c in cookies:
                try:
                    self.driver.add_cookie(c)
                except Exception:
                    continue
            return True
        except Exception:
            return False

    # ---- Adaptive pacing ----
    def _pace(self, fast: bool = False) -> None:
        try:
            target = self._pace_fast_ms if fast else self._pace_slow_ms
            elapsed = (time.time() - self._last_action_ts) * 1000.0
            sleep_ms = max(0.0, target - elapsed)
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
            self._last_action_ts = time.time()
        except Exception:
            pass
    
    def _short_wait(self, timeout: float = 6.0) -> WebDriverWait:
        """Return a shorter WebDriverWait helper for optional UI elements."""
        try:
            timeout = float(timeout)
        except Exception:
            timeout = 6.0
        if timeout <= 0:
            timeout = 1.0
        return WebDriverWait(self.driver, timeout)

    def _select_relaxed(self, select_el, candidates) -> bool:
        """Select dropdown option using relaxed matching rules."""
        try:
            dropdown = Select(select_el)
            options = dropdown.options
        except Exception:
            return False
        texts = [(opt.text or "").strip() for opt in options]
        lowers = [t.lower() for t in texts]

        for cand in candidates or []:
            if not cand:
                continue
            normalized = str(cand).strip()
            if not normalized:
                continue
            lower = normalized.lower()
            if lower in lowers:
                try:
                    dropdown.select_by_index(lowers.index(lower))
                    return True
                except Exception:
                    continue

        for cand in candidates or []:
            if not cand:
                continue
            lower = str(cand).strip().lower()
            if not lower:
                continue
            for idx_opt, text_opt in enumerate(lowers):
                if lower in text_opt:
                    try:
                        dropdown.select_by_index(idx_opt)
                        return True
                    except Exception:
                        continue

        for cand in candidates or []:
            if not cand:
                continue
            lower = str(cand).strip().lower()
            if not lower:
                continue
            for idx_opt, text_opt in enumerate(lowers):
                if text_opt.startswith(lower):
                    try:
                        dropdown.select_by_index(idx_opt)
                        return True
                    except Exception:
                        continue
        return False

    def _try_pick_autocomplete(self, input_el, wait=None, desired_text: str = None) -> bool:
        """Pick the first visible autocomplete suggestion, favouring desired_text."""
        try:
            time.sleep(1.0)
            suggestion_queries = [
                "//ul[contains(@class,'ui-autocomplete') and contains(@style,'display: block')]//li[1]",
                "//ul[contains(@class,'ui-autocomplete')]//li[1]",
                "//li[contains(@class,'ui-menu-item')][1]",
                "//div[contains(@class,'autocomplete') or contains(@class,'suggest')]//li[1]",
            ]

            if desired_text:
                try:
                    items = self.driver.find_elements(
                        By.XPATH,
                        "//ul[contains(@class,'ui-autocomplete')]//li | //li[contains(@class,'ui-menu-item')] | //div[contains(@class,'autocomplete') or contains(@class,'suggest')]//li",
                    )
                    target_words = desired_text.lower().split()
                    for it in items:
                        try:
                            if not it.is_displayed():
                                continue
                            snippet = (it.text or "").strip().lower()
                            if not snippet:
                                continue
                            if target_words and all(word in snippet for word in target_words[:2]):
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", it)
                                time.sleep(0.1)
                                self.driver.execute_script("arguments[0].click();", it)
                                return True
                        except Exception:
                            continue
                except Exception:
                    pass

            for query in suggestion_queries:
                try:
                    el = self.driver.find_element(By.XPATH, query)
                    if not el.is_displayed():
                        continue
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
                    time.sleep(0.1)
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
                except Exception:
                    continue

            try:
                input_el.send_keys("\ue015")  # ArrowDown
                time.sleep(0.1)
                input_el.send_keys("\ue007")  # Enter
                return True
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _dismiss_common_popups(self, extra_selectors=None) -> int:
        """Best-effort dismissal for cookie banners and overlays."""
        driver = self.driver
        selectors = [
            "[class*='cookie']",
            "[id*='cookie']",
            "[class*='consent']",
            "[class*='gdpr']",
            "[class*='overlay']",
            "[class*='modal']",
            "[data-testid*='cookie']",
        ]
        if extra_selectors:
            selectors.extend(extra_selectors)

        dismissed = 0
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            for element in elements:
                try:
                    if not element.is_displayed():
                        continue
                    driver.execute_script("arguments[0].style.display='none';", element)
                    dismissed += 1
                except Exception:
                    continue

        action_xpaths = [
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'agree')]",
            "//button[contains(@class,'close') or contains(.,'×') or contains(.,'Close')]",
            "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
            "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]",
        ]
        for xp in action_xpaths:
            try:
                btn = driver.find_element(By.XPATH, xp)
                if not btn.is_displayed():
                    continue
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    try:
                        btn.click()
                    except Exception:
                        continue
                dismissed += 1
            except Exception:
                continue

        if dismissed:
            print(f"🍪 Dismissed {dismissed} popups/overlays")
        return dismissed


    def _load_credentials(self) -> tuple[str, str]:
        """Load platform credentials from environment variables"""
        load_dotenv()
        user = os.getenv(f"{self.PLATFORM.upper()}_USERNAME")
        pwd = os.getenv(f"{self.PLATFORM.upper()}_PASSWORD")
        if not user or not pwd:
            raise RuntimeError(f"Missing credentials for {self.PLATFORM}")
        return user, pwd
    
    def login_with_2fa(self, job_id: Optional[str] = None) -> bool:
        """Enhanced login with 2FA support"""
        if not self.LOGIN_URL:
            raise NotImplementedError("LOGIN_URL must be defined")
            
        driver = self.driver
        driver.get(self.LOGIN_URL)
        self._capture_step("login_page", f"Opened login page: {self.LOGIN_URL}")
        wait = WebDriverWait(driver, 20)
        self.manual_job_id = job_id
        if job_id:
            try:
                manual_2fa_prepare(job_id, platform=self.PLATFORM.lower())
            except Exception:
                pass
        
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
            
            # Submit login (avoid invalid :contains CSS; CSS first, then XPath fallbacks)
            try:
                submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                submit.click()
            except Exception:
                try:
                    submit = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit'] | //button[contains(.,'Login') or contains(.,'Sign in') or contains(.,'Sign In')] | //a[contains(.,'Login') or contains(.,'Sign in') or contains(.,'Sign In')]")
                    submit.click()
                except Exception:
                    try:
                        pass_field.send_keys("\n")
                    except Exception:
                        pass
            self._capture_step("login_submitted", "Submitted login form")
            
            # Check for 2FA
            if self._check_for_2fa():
                print(f"📱 2FA required for {self.PLATFORM}")
                return self._handle_2fa(job_id=job_id)
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
            
            # Submit code (CSS first, then XPath text fallbacks)
            submitted = False
            for sel in ["button[type='submit']", "input[type='submit']"]:
                try:
                    sub = self.driver.find_element(By.CSS_SELECTOR, sel)
                    sub.click()
                    submitted = True
                    print("✅ Submitted 2FA code")
                    break
                except Exception:
                    continue
            if not submitted:
                for xp in [
                    "//button[contains(.,'Verify') or contains(.,'Submit') or contains(.,'Continue')]",
                    "//input[@type='submit']"
                ]:
                    try:
                        sub = self.driver.find_element(By.XPATH, xp)
                        sub.click()
                        submitted = True
                        print("✅ Submitted 2FA code")
                        break
                    except Exception:
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
            # GSMX: avoid generic words (e.g., 'phones' appears on public pages). Use account/offer cues.
            'gsmexchange': [
                'my account', 'my offers', 'logout', 'add offer', 'new offer', 'post offers', 'trading'
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
        """GSM Exchange robust login with improved selectors and timeout handling."""
        driver = self.driver
        driver.get(self.LOGIN_URL)
        self._capture_step("gsmx_login_page", f"Opened login page: {self.LOGIN_URL}")
        wait = WebDriverWait(driver, 30)
        
        try:
            print(f"🔐 Logging into {self.PLATFORM}...")
            
            # Wait for page to fully load
            time.sleep(3)
            self._dismiss_gsmx_popups()
            self._dismiss_common_popups(['.cc-window', '.modal', '#cookie-banner'])
            
            # Try multiple username selectors (from test file)
            username_selectors = [
                "input[name='email']",
                "input[name='username']", 
                "input[type='email']",
                "input[placeholder*='email']",
                "input[placeholder*='username']",
                "#email",
                "#username"
            ]
            
            user_field = None
            for selector in username_selectors:
                try:
                    user_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Found username field: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not user_field:
                print("❌ Could not find username field with any selector")
                self._capture_step("gsmx_no_username_field", "Username field not found")
                return False
            
            user_field.clear()
            user_field.send_keys(self.username)
            print("✅ Username entered")
            
            # Try multiple password selectors
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "#password"
            ]
            
            pass_field = None
            for selector in password_selectors:
                try:
                    pass_field = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found password field: {selector}")
                    break
                except Exception:
                    continue
            
            if not pass_field:
                print("❌ Could not find password field")
                self._capture_step("gsmx_no_password_field", "Password field not found")
                return False
            
            pass_field.clear()
            pass_field.send_keys(self.password)
            print("✅ Password entered")
            self._capture_step("gsmx_login_filled", "Filled GSM Exchange credentials")
            
            # Try multiple submit selectors
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']", 
                "[onclick*='login']",
                "[onclick*='signin']"
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit = driver.find_element(By.CSS_SELECTOR, selector)
                    submit.click()
                    submitted = True
                    print(f"✅ Form submitted using: {selector}")
                    break
                except Exception:
                    continue
            
            if not submitted:
                # Try Enter key as fallback
                try:
                    pass_field.send_keys("\n")
                    print("✅ Form submitted using Enter key")
                except Exception:
                    pass
            
            self._capture_step("gsmx_login_submitted", "Submitted GSM Exchange login")
            
            # Wait for potential redirect
            time.sleep(5)
            
            # Check current URL and page state
            current_url = driver.current_url
            print(f"📍 Current URL after login: {current_url}")
            
            # Check for 2FA
            page_text = driver.page_source.lower()
            needs_2fa = any(k in page_text for k in [
                "verification", "verify your identity", "2fa", "enter code", "security code", "authentication code"
            ])
            
            if needs_2fa:
                print(f"📱 2FA required for {self.PLATFORM}")
                self._capture_step("gsmx_2fa_page", "GSM Exchange 2FA verification page detected")
                return self._handle_gsmx_2fa()
            else:
                # Check if login successful
                if self._check_login_success():
                    print(f"✅ Logged into {self.PLATFORM} successfully")
                    self._capture_step("gsmx_login_success", "Logged in to GSM Exchange")
                    return True
                else:
                    print(f"❌ Login failed for {self.PLATFORM}")
                    print(f"⚠️  Current URL: {current_url}")
                    return False
                
        except TimeoutException as e:
            print(f"❌ Login timeout for {self.PLATFORM}: {e}")
            self._capture_step("gsmx_login_timeout", f"Login timeout: {e}")
            return False
        except Exception as e:
            print(f"❌ Login error for {self.PLATFORM}: {e}")
            self._capture_step("gsmx_login_error", f"Login error: {e}")
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

    # ---- Fast sidebar-driven posting (mirrors Cellpex speed) ----
    def _select_relaxed_text(self, select_el, candidates: list[str]) -> bool:
        """Select an option from <select> using relaxed matching (exact, contains, startswith)."""
        try:
            dd = Select(select_el)
            opts = dd.options
            texts = [(o.text or '').strip() for o in opts]
            lowers = [t.lower() for t in texts]
            # exact (case-insensitive)
            for c in candidates:
                if not c:
                    continue
                c2 = str(c).strip()
                if c2.lower() in lowers:
                    dd.select_by_index(lowers.index(c2.lower()))
                    return True
            # contains
            for c in candidates:
                if not c:
                    continue
                cl = str(c).strip().lower()
                for i, t in enumerate(lowers):
                    if cl and cl in t:
                        dd.select_by_index(i)
                        return True
            # startswith
            for c in candidates:
                if not c:
                    continue
                cl = str(c).strip().lower()
                for i, t in enumerate(lowers):
                    if cl and t.startswith(cl):
                        dd.select_by_index(i)
                        return True
        except Exception:
            pass
        return False

    def _sidebar_and_form(self, action_contains: str, timeout: int = 10):
        """Find `.s-sidebar` and inside it a form whose action contains the substring."""
        driver = self.driver
        try:
            sb = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".s-sidebar")))
        except Exception:
            try:
                sb = driver.find_element(By.CSS_SELECTOR, ".s-sidebar")
            except Exception:
                return None, None
        try:
            frm = sb.find_element(By.CSS_SELECTOR, f"form[action*='{action_contains}']")
            return sb, frm
        except Exception:
            return sb, None

    def _navigate_section(self, section: str) -> tuple:
        """Navigate to a GSMX section and return (sidebar, form) if found quickly."""
        driver = self.driver
        self._dismiss_gsmx_popups()
        candidates = []
        if section == 'phones':
            candidates = [
                "https://www.gsmexchange.com/en/phones?tab=offers",
                "https://www.gsmexchange.com/en/phones",
                "https://www.gsmexchange.com/en/trading/add-offer",
                "https://www.gsmexchange.com/gsm/post_offers.html",
            ]
            action_hint = "/offers"
        elif section == 'accessories':
            candidates = [
                "https://www.gsmexchange.com/en/phones?tab=accessories",
                "https://www.gsmexchange.com/en/accessories"
            ]
            action_hint = "/accessories"
        elif section == 'used':
            candidates = [
                "https://www.gsmexchange.com/en/phones?tab=used",
                "https://www.gsmexchange.com/en/refurbished",
                "https://www.gsmexchange.com/en/phones?tab=refurbished",
            ]
            action_hint = "/refurbished"
        else:  # consumer
            candidates = ["https://www.gsmexchange.com/en/consumer"]
            action_hint = "/consumer"

        for url in candidates:
            try:
                driver.get(url)
                time.sleep(1.2)
                self._dismiss_gsmx_popups()
                sb, frm = self._sidebar_and_form(action_hint)
                if sb and frm:
                    self._capture_step(f"gsmx_{section}_form_found", f"Found form at {url}")
                    return sb, frm
            except Exception:
                continue
        return None, None

    def _post_sidebar_phones(self, sb, row) -> str | None:
        driver = self.driver
        try:
            # Ensure Sell selected
            try:
                sell = sb.find_element(By.CSS_SELECTOR, "#typeSell")
                driver.execute_script("arguments[0].click();", sell)
            except Exception:
                pass

            # Model autocompleter (robust selectors + suggestion pick)
            model = str(row.get("product_name") or row.get("model") or row.get("model_code") or "").strip()
            brand = str(row.get("brand") or "").strip()
            query = f"{brand} {model}".strip() or model or brand
            try:
                inp = None
                # Try multiple selectors inside sidebar
                for sel in [
                    "input[name='phModelFull']",
                    "form[action*='/offers'] input[name='phModelFull']",
                    "input[data-component='trading/phoneAutocompleter']",
                    ".twitter-typeahead input.tt-query",
                ]:
                    try:
                        inp = sb.find_element(By.CSS_SELECTOR, sel)
                        break
                    except Exception:
                        continue
                if inp:
                    inp.clear()
                    for chunk in (query or "").split(" "):
                        inp.send_keys(chunk + " ")
                        time.sleep(0.15)
                    time.sleep(0.8)
                    # Try suggestions by click
                    try:
                        sug = driver.find_element(By.XPATH, "//div[contains(@class,'tt-menu') or contains(@class,'autocomplete') or contains(@class,'suggest')]//div|//ul[contains(@class,'ui-autocomplete')]//li[1]")
                        if sug and sug.is_displayed():
                            driver.execute_script("arguments[0].click();", sug)
                    except Exception:
                        pass
                    # Keyboard fallback
                    try:
                        inp.send_keys("\ue015"); time.sleep(0.05); inp.send_keys("\ue007")
                    except Exception:
                        pass
            except Exception:
                pass

            # Quantity
            try:
                qty_val = str(row.get("quantity", "1"))
                qty = sb.find_element(By.CSS_SELECTOR, "#f-at-qty, input[name='phQty']")
                qty.clear(); qty.send_keys(qty_val)
            except Exception:
                pass

            # Currency
            try:
                currency = (str(row.get("currency", "USD")).upper())
                cur = sb.find_element(By.CSS_SELECTOR, "#f-at-currency, select[name='phCurrency']")
                ok = False
                try:
                    Select(cur).select_by_visible_text(currency)
                    ok = True
                except Exception:
                    ok = self._select_relaxed_text(cur, [currency, "USD", "US Dollar", "$", "EUR", "GBP"])
                if ok:
                    self._capture_step("gsmx_currency_set", currency)
            except Exception:
                pass

            # Price
            try:
                price_val = str(row.get("price", ""))
                pr = sb.find_element(By.CSS_SELECTOR, "#f-at-price, input[name='phPrice']")
                pr.clear(); pr.send_keys(price_val)
            except Exception:
                pass

            # Condition
            try:
                cond_map = {
                    "new": "New",
                    "used": "Used and tested",
                    "refurbished": "Refurbished",
                    "asis": "ASIS",
                    "7 day / 14 day": "7 day / 14 day",
                    "cpo": "CPO",
                    "pre order": "Pre order",
                }
                cond_in = str(row.get("condition", "New")).strip().lower()
                desired = cond_map.get(cond_in, row.get("condition", "New"))
                sel = sb.find_element(By.CSS_SELECTOR, "#f-at-condition, select[name='phCondition']")
                try:
                    Select(sel).select_by_visible_text(desired)
                except Exception:
                    self._select_relaxed_text(sel, [desired])
            except Exception:
                pass

            # Spec
            try:
                spec_map = {
                    "US": "US spec.", "USA": "US spec.", "Euro": "Euro spec.", "EU": "Euro spec.",
                    "UK": "UK spec.", "Asia": "Asia spec.", "Arabic": "Arab spec.", "Other": "Other spec.",
                    "India": "Indian spec.", "African": "African spec.", "Latin": "Latin spec.",
                    "Japan": "Japanese spec.", "China": "China spec.", "Australia": "Australia spec.",
                    "Canada": "Canada Spec.", "Global": "Global Spec."
                }
                raw = str(row.get("market_spec", row.get("market", "US")))
                desired = spec_map.get(raw, spec_map.get(raw.upper(), "Global Spec."))
                sel = sb.find_element(By.CSS_SELECTOR, "#f-at-spec, select[name='phSpec']")
                try:
                    Select(sel).select_by_visible_text(desired)
                except Exception:
                    self._select_relaxed_text(sel, [desired])
            except Exception:
                pass

            # Comments
            try:
                txt = sb.find_element(By.CSS_SELECTOR, "#comments, textarea[name='phComments']")
                comments = row.get("description") or ""
                if not comments:
                    comments = f"Condition: {row.get('condition','')} | Memory: {row.get('memory','')} | Color: {row.get('color','')}"
                txt.clear(); txt.send_keys(str(comments)[:1000])
            except Exception:
                pass

            # Confirm stock
            try:
                cb = sb.find_element(By.CSS_SELECTOR, "#f-at-confirm, input[name='confirm']")
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
            except Exception:
                pass

            # Submit (broaden selectors and attempt JS submit if needed)
            try:
                btn = None
                for sel in [
                    "button.primary.c-tOR-item[type='submit']",
                    "button[type='submit'].primary",
                    "input[type='submit']",
                    "button.c-tOR-item[type='submit']",
                ]:
                    try:
                        btn = sb.find_element(By.CSS_SELECTOR, sel)
                        break
                    except Exception:
                        continue
                if btn:
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", btn)
                    self._capture_step("gsmx_submit", "Clicked New offer (fast)")
                else:
                    # Fallback to submitting the form directly
                    try:
                        frm = sb.find_element(By.CSS_SELECTOR, "form[action*='/offers']")
                        driver.execute_script("if(arguments[0]){arguments[0].requestSubmit ? arguments[0].requestSubmit() : arguments[0].submit();}", frm)
                        self._capture_step("gsmx_submit_form", "Submitted form via requestSubmit")
                    except Exception:
                        pass
            except Exception:
                pass

            time.sleep(4)
            # Verify
            if self._verify_gsmx_listing(row):
                return "Success: GSM Exchange offer posted (fast)"
            page = (driver.page_source or '').lower()
            if any(k in page for k in ["offer created", "new offer", "offer posted", "successfully"]):
                return "Success: GSM Exchange offer posted"
            return "Pending: Submitted offer; waiting for confirmation"
        except Exception:
            return None

    def _post_sidebar_accessories(self, sb, row) -> str | None:
        driver = self.driver
        try:
            # Sell radio
            try:
                sell = sb.find_element(By.CSS_SELECTOR, "#typeSell")
                driver.execute_script("arguments[0].click();", sell)
            except Exception:
                pass
            # Brand select
            try:
                brand = str(row.get("brand", "Apple"))
                sel = sb.find_element(By.CSS_SELECTOR, "select[name='phBrand']")
                ok = False
                try:
                    Select(sel).select_by_visible_text(brand)
                    ok = True
                except Exception:
                    ok = self._select_relaxed_text(sel, [brand])
                if not ok:
                    try:
                        Select(sel).select_by_index(1)
                    except Exception:
                        pass
            except Exception:
                pass
            # Original checkbox
            try:
                if bool(row.get("original", True)):
                    cb = sb.find_element(By.CSS_SELECTOR, "#atOriginal, input[name='atOriginal']")
                    if not cb.is_selected():
                        driver.execute_script("arguments[0].click();", cb)
            except Exception:
                pass
            # Accessory type
            try:
                acc_type = str(row.get("accessory_type") or row.get("category") or "Other accessories")
                sel = sb.find_element(By.CSS_SELECTOR, "select[name='atType']")
                if not self._select_relaxed_text(sel, [acc_type]):
                    try:
                        Select(sel).select_by_index(1)
                    except Exception:
                        pass
            except Exception:
                pass
            # Submit
            try:
                btn = sb.find_element(By.CSS_SELECTOR, "button.primary.c-tOR-item[type='submit'], input[type='submit']")
                driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                time.sleep(0.1)
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass
            time.sleep(2)
            return "Pending: Accessories offer submitted"
        except Exception:
            return None

    def _post_sidebar_used(self, sb, row) -> str | None:
        driver = self.driver
        try:
            # Subcategory radio
            try:
                cond = str(row.get("condition", "Used")).lower()
                radio_id = "noticeSubcategoryRefurbished" if "refurb" in cond else "noticeSubcategoryUsed"
                r = sb.find_element(By.CSS_SELECTOR, f"#{radio_id}")
                driver.execute_script("arguments[0].click();", r)
            except Exception:
                pass
            # Brand select
            try:
                brand = str(row.get("brand", "Apple"))
                sel = sb.find_element(By.CSS_SELECTOR, "select[name='phBrand']")
                if not self._select_relaxed_text(sel, [brand]):
                    try:
                        Select(sel).select_by_index(1)
                    except Exception:
                        pass
            except Exception:
                pass
            # Submit
            try:
                btn = sb.find_element(By.CSS_SELECTOR, "button.primary.c-tOR-item[type='submit'], input[type='submit']")
                driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                time.sleep(0.1)
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass
            time.sleep(2)
            return "Pending: Used/Refurbished offer submitted"
        except Exception:
            return None

    def _post_sidebar_consumer(self, sb, row) -> str | None:
        driver = self.driver
        try:
            # Category
            try:
                cat = str(row.get("category") or "General Product (Other)")
                sel = sb.find_element(By.CSS_SELECTOR, "#ctCategory, select[name='ctCategory']")
                if not self._select_relaxed_text(sel, [cat, "General", "Other"]):
                    try:
                        Select(sel).select_by_index(1)
                    except Exception:
                        pass
            except Exception:
                pass
            # Manufacturer and Model may be dynamically loaded; skip if empty
            # Quantity
            try:
                qty_val = str(row.get("quantity", "1"))
                q = sb.find_element(By.CSS_SELECTOR, "#f-at-qty, input[name='ctQty']")
                q.clear(); q.send_keys(qty_val)
            except Exception:
                pass
            # Currency
            try:
                currency = (str(row.get("currency", "USD")).upper())
                cur = sb.find_element(By.CSS_SELECTOR, "#f-at-currency, select[name='ctCurrency']")
                ok = False
                try:
                    Select(cur).select_by_visible_text(currency)
                    ok = True
                except Exception:
                    ok = self._select_relaxed_text(cur, [currency, "USD", "US Dollar", "$", "EUR", "GBP"])
                if ok:
                    self._capture_step("gsmx_consumer_currency", currency)
            except Exception:
                pass
            # Price
            try:
                price_val = str(row.get("price", ""))
                p = sb.find_element(By.CSS_SELECTOR, "#f-at-price, input[name='ctPrice']")
                p.clear(); p.send_keys(price_val)
            except Exception:
                pass
            # Confirm
            try:
                cb = sb.find_element(By.CSS_SELECTOR, "#f-at-confirm, input[name='confirm']")
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
            except Exception:
                pass
            # Submit
            try:
                btn = sb.find_element(By.CSS_SELECTOR, "button.primary.c-tOR-item[type='submit'], input[type='submit']")
                driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                time.sleep(0.1)
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass
            time.sleep(2)
            return "Pending: Consumer offer submitted"
        except Exception:
            return None

    def _post_listing_via_sidebar(self, row) -> str | None:
        """Fast-path posting using the visible sidebar forms on known GSMX pages."""
        # Decide section
        section = "phones"
        try:
            ptype = str(row.get("product_type", "phone")).lower()
            category = str(row.get("category", "")).lower()
            cond = str(row.get("condition", "")).lower()
            if "consumer" in ptype or "consumer" in category:
                section = "consumer"
            elif "accessor" in ptype or "gadget" in ptype or "accessor" in category or "gadget" in category:
                section = "accessories"
            elif any(k in cond for k in ["used", "refurb"]):
                section = "used"
        except Exception:
            section = "phones"

        sb, frm = self._navigate_section(section)
        if not (sb and frm):
            return None

        # Route to section-specific filler
        if section == 'phones':
            return self._post_sidebar_phones(sb, row)
        if section == 'accessories':
            return self._post_sidebar_accessories(sb, row)
        if section == 'used':
            return self._post_sidebar_used(sb, row)
        return self._post_sidebar_consumer(sb, row)

    def _open_offer_form(self) -> bool:
        """Navigate to a working Add Offer form. Returns True if the model input is present."""
        driver = self.driver
        wait = WebDriverWait(driver, 40)

        def _found_offer_form_here(context_label: str = "") -> bool:
            """Detect offer form inputs in current browsing context (no frame switching)."""
            try:
                # Primary model input selectors
                selectors = [
                    (By.NAME, "phModelFull"),
                    (By.CSS_SELECTOR, "form[action*='/offers'] input[name='phModelFull']"),
                    (By.CSS_SELECTOR, "form[action*='add-offer'] input[name='phModelFull']"),
                    (By.CSS_SELECTOR, "input[data-component='trading/phoneAutocompleter']"),
                    (By.CSS_SELECTOR, ".twitter-typeahead input.tt-query"),
                ]
                for by, sel in selectors:
                    try:
                        wait.until(EC.presence_of_element_located((by, sel)))
                        self._capture_step("gsmx_offer_form", f"Offer form ready {('('+context_label+')') if context_label else ''}")
                        return True
                    except Exception:
                        continue
                # Fallback: some forms expose other known fields even if model is delayed
                for by, sel in [
                    (By.NAME, "phQty"),
                    (By.NAME, "phPrice"),
                    (By.NAME, "phCurrency"),
                    (By.NAME, "phCondition"),
                    (By.NAME, "phComments"),
                ]:
                    try:
                        el = driver.find_element(by, sel)
                        if el and el.is_displayed():
                            self._capture_step("gsmx_offer_form_partial", f"Offer form fields present {('('+context_label+')') if context_label else ''}")
                            return True
                    except Exception:
                        continue
                return False
            except Exception:
                return False

        def _scan_all_iframes_for_form() -> bool:
            """Switch into each iframe and try to detect the offer form."""
            try:
                frames = driver.find_elements(By.TAG_NAME, "iframe")
            except Exception:
                frames = []
            for idx, fr in enumerate(frames[:8]):  # limit to first 8 frames
                try:
                    driver.switch_to.frame(fr)
                    if _found_offer_form_here(context_label=f"in iframe #{idx}"):
                        driver.switch_to.default_content()
                        return True
                except Exception:
                    pass
                finally:
                    try:
                        driver.switch_to.default_content()
                    except Exception:
                        pass
            return False

        def _click_ctas_then_check() -> bool:
            """Click likely Add Offer CTAs/tabs and then re-check for the form."""
            candidates = [
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add offer')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add offer')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'post offers')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'post offers')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'new offer')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'new offer')]",
                "//button[contains(.,'Offer') or contains(.,'offer')]",
                "//a[contains(.,'Offer') or contains(.,'offer')]",
                "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sell')]",
                "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sell')]",
            ]
            for xp in candidates:
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if el and el.is_displayed():
                        try:
                            self._human_click(el)
                        except Exception:
                            try:
                                driver.execute_script("arguments[0].click();", el)
                            except Exception:
                                continue
                        time.sleep(1.2)
                        if _found_offer_form_here(context_label="after CTA click"):
                            return True
                        if _scan_all_iframes_for_form():
                            return True
                except Exception:
                    continue
            return False
        # First try explicit destinations that commonly redirect to the company offers UI
        try:
            driver.get("https://www.gsmexchange.com/en/trading/my-offers")
            time.sleep(2)
            self._dismiss_gsmx_popups()
            if _found_offer_form_here(context_label="at /en/trading/my-offers"):
                return True
            if _scan_all_iframes_for_form():
                return True
            if _click_ctas_then_check():
                return True
            # If not found, look for a direct link to /en/company/*/offers in the nav and follow it
            try:
                link = None
                for sel in [
                    "a[href*='/en/company/'][href$='/offers']",
                    "a[href*='/en/company/'][href*='/offers']",
                    "a[href*='/offers']",
                ]:
                    try:
                        link = driver.find_element(By.CSS_SELECTOR, sel)
                        if link:
                            break
                    except Exception:
                        continue
                if link:
                    href = link.get_attribute("href")
                    if href:
                        driver.get(href)
                        time.sleep(2)
                        self._dismiss_gsmx_popups()
                        if _found_offer_form_here(context_label=f"at {href}"):
                            return True
                        if _scan_all_iframes_for_form():
                            return True
                        if _click_ctas_then_check():
                            return True
            except Exception:
                pass
        except Exception:
            pass

        candidates = [
            "https://www.gsmexchange.com/en/phones",
            "https://www.gsmexchange.com/en/phones?tab=offers",
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
                # On generic pages, try to find a link to the company offers page as well
                try:
                    link = None
                    for sel in [
                        "a[href*='/en/company/'][href$='/offers']",
                        "a[href*='/en/company/'][href*='/offers']",
                        "a[href*='/offers']",
                    ]:
                        try:
                            link = driver.find_element(By.CSS_SELECTOR, sel)
                            if link:
                                break
                        except Exception:
                            continue
                    if link:
                        href = link.get_attribute("href")
                        if href:
                            driver.get(href)
                            time.sleep(2)
                            self._dismiss_gsmx_popups()
                except Exception:
                    pass
                if _found_offer_form_here(context_label=f"at {url}"):
                    return True
                if _scan_all_iframes_for_form():
                    return True
                if _click_ctas_then_check():
                    return True
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
        """Post listing on GSM Exchange using a resilient Cellpex-style flow."""
        driver = self.driver
        short_wait = self._short_wait(8)

        def find(locator):
            try:
                return driver.find_element(*locator)
            except Exception:
                try:
                    return self._short_wait(6).until(EC.presence_of_element_located(locator))
                except Exception:
                    return None

        try:
            print("📍 Navigating to GSM Exchange Add Offer page...")
            driver.get("https://www.gsmexchange.com/en/phones?tab=offers")
            self._capture_step("gsmx_offer_page", "Opened GSM Exchange offer page")
            time.sleep(2)
            self._dismiss_common_popups(['.cc-window', '.modal', '#cookie-banner'])
            try:
                self._short_wait(10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form")))
            except Exception:
                pass

            for locator in [
                (By.CSS_SELECTOR, '#typeSell'),
                (By.CSS_SELECTOR, "input[name='isOffer'][value='1']"),
                (By.NAME, 'isOffer'),
            ]:
                sell_radio = find(locator)
                if sell_radio:
                    try:
                        sell_radio.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", sell_radio)
                        except Exception:
                            continue
                    self._capture_step("gsmx_sell_selected", "Selected sell offer radio")
                    break

            brand = str(row.get("brand") or "").strip()
            product_name = str(row.get("product_name") or row.get("model") or row.get("model_code") or "").strip()
            query = f"{brand} {product_name}".strip() if brand and product_name else (product_name or brand)

            model_input = find((By.NAME, "phModelFull"))
            if model_input and query:
                try:
                    model_input.clear()
                except Exception:
                    pass
                model_input.send_keys(query)
                self._capture_step("gsmx_model_filled", f"Model: {query}")
                try:
                    self._try_pick_autocomplete(model_input, short_wait, query)
                except Exception:
                    pass

            qty_value = str(row.get("quantity") or "1")
            qty_field = find((By.NAME, "phQty"))
            if qty_field:
                try:
                    qty_field.clear()
                except Exception:
                    pass
                qty_field.send_keys(qty_value)
                self._capture_step("gsmx_qty_filled", f"Quantity: {qty_value}")

            currency = str(row.get("currency") or "USD").strip().upper()
            currency_field = find((By.NAME, "phCurrency"))
            if currency_field:
                if not self._select_relaxed(currency_field, [currency, currency.upper(), currency.lower()]):
                    try:
                        Select(currency_field).select_by_index(1)
                    except Exception:
                        pass
                self._capture_step("gsmx_currency_filled", f"Currency: {currency}")

            price_raw = row.get("price", "")
            price_field = find((By.NAME, "phPrice"))
            if price_field:
                price_text = ''.join(ch for ch in str(price_raw) if ch.isdigit() or ch in '.,')
                try:
                    price_field.clear()
                except Exception:
                    pass
                if price_text:
                    price_field.send_keys(price_text)
                self._capture_step("gsmx_price_filled", f"Price: {price_text or price_raw}")

            condition = str(row.get("condition") or "New").strip()
            condition_field = find((By.NAME, "phCondition"))
            if condition_field:
                cond_candidates = [condition, condition.title(), condition.upper()]
                if not self._select_relaxed(condition_field, cond_candidates):
                    try:
                        Select(condition_field).select_by_index(1)
                    except Exception:
                        pass
                self._capture_step("gsmx_condition_filled", f"Condition: {condition}")

            description = row.get("description") or f"High quality {brand or 'device'} in {row.get('condition', 'excellent')} condition"
            comments_field = find((By.NAME, "phComments"))
            if comments_field and description:
                try:
                    comments_field.clear()
                except Exception:
                    pass
                comments_field.send_keys(str(description)[:900])
                self._capture_step("gsmx_description_filled", "Description entered")

            confirm_cb = find((By.NAME, "confirm"))
            if confirm_cb and not confirm_cb.is_selected():
                try:
                    confirm_cb.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", confirm_cb)
                    except Exception:
                        pass
                self._capture_step("gsmx_confirm_stock", "Confirmed physical stock")

            submitted = False
            for locator in [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
            ]:
                try:
                    submit_btn = short_wait.until(EC.element_to_be_clickable(locator))
                except Exception:
                    submit_btn = find(locator)
                if not submit_btn:
                    continue
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", submit_btn)
                except Exception:
                    pass
                try:
                    submit_btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", submit_btn)
                    except Exception:
                        continue
                submitted = True
                self._capture_step("gsmx_submitted", "Submitted GSM Exchange offer")
                break

            if not submitted:
                return "Error: Could not submit GSM Exchange offer"

            time.sleep(2.5)
            page_text = driver.page_source.lower()

            success_keywords = ["offer created", "offer posted", "thank you", "success"]
            review_keywords = ["pending moderation", "awaiting review", "submitted for approval", "under review"]
            error_keywords = ["error", "required", "invalid", "please fill", "please select", "must select"]

            if any(keyword in page_text for keyword in error_keywords):
                inline_errors = self._read_inline_errors()
                self._capture_step("gsmx_error", inline_errors or "Form submission error")
                message = "Error: Form submission failed"
                if inline_errors:
                    message += f" - {inline_errors}"
                return message

            verified = self._verify_gsmx_listing(row)
            if any(keyword in page_text for keyword in success_keywords) or verified:
                if verified:
                    self._capture_step("gsmx_success", "GSM Exchange offer posted and verified")
                    return "Success: GSM Exchange offer posted and verified"
                self._capture_step("gsmx_success", "GSM Exchange offer posted")
                return "Pending: Offer submitted; verification pending"

            if any(keyword in page_text for keyword in review_keywords):
                if verified:
                    return "Success: Submitted for review and visible in account"
                return "Pending: Submission under review"

            if verified:
                self._capture_step("gsmx_success", "Offer verified post submission")
                return "Success: Offer appears in account"

            return "Pending: Submitted offer; waiting for confirmation"

        except TimeoutException:
            return "Timeout posting listing"
        except Exception as exc:
            self._capture_step("gsmx_exception", str(exc))
            return f"Error: {exc}"


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
    # Other platforms registered below
}


class EnhancedKardofPoster(Enhanced2FAMarketplacePoster):
    """Kadorf/Kardof poster using fast, Cellpex-like direct form fill.

    - Optimizes for speed by reducing waits and batching field updates
    - Uses relaxed dropdown matching and resilient submit methods
    - Keeps anti-hallucination: only report success when page indicates it
    """
    PLATFORM = "KARDOF"
    LOGIN_URL = "https://www.kardof.com/login"

    def login_with_2fa(self) -> bool:
        """Kadorf simple login - replicate Cellpex's direct approach."""
        driver = self.driver
        driver.get(self.LOGIN_URL)
        self._capture_step("kadorf_login_page", f"Opened login page: {self.LOGIN_URL}")
        self._dismiss_common_popups(['.cookie', '.modal', '#cookie-banner'])
        wait = WebDriverWait(driver, 20)
        
        try:
            print(f"🔐 Logging into {self.PLATFORM}...")
            
            # Kadorf-specific selectors (like Cellpex directness)
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.clear()
            email_field.send_keys(self.username)
            
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            password_field.clear()
            password_field.send_keys(self.password)
            self._capture_step("kadorf_login_filled", "Filled Kadorf credentials")
            
            # Submit login
            submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'].y-button")))
            submit.click()
            self._capture_step("kadorf_login_submitted", "Submitted Kadorf login")
            
            # Wait for potential redirect
            time.sleep(3)
            
            # Check if login successful (like Cellpex approach)
            current_url = driver.current_url
            if "login" not in current_url:
                if self._check_login_success():
                    print(f"✅ Logged into {self.PLATFORM} successfully")
                    self._capture_step("kadorf_login_success", "Logged in to Kadorf")
                    return True
                else:
                    print(f"❌ Login failed for {self.PLATFORM}")
                    return False
            else:
                print(f"❌ Still on login page for {self.PLATFORM}")
                return False
                
        except TimeoutException:
            print(f"❌ Login timeout for {self.PLATFORM}")
            self._capture_step("kadorf_login_timeout", "Login timeout")
            return False
        except Exception as e:
            print(f"❌ Login error for {self.PLATFORM}: {e}")
            self._capture_step("kadorf_login_error", f"{e}")
            return False


    def _fill_kadorf_form(self, row, wait) -> bool:
        """Fill Kadorf sell form fields quickly with relaxed fallbacks."""
        driver = self.driver
        try:
            # Pre-extract values
            category = str(row.get("category") or row.get("product_type") or "Mobile Phones")
            condition = str(row.get("condition", "New"))
            currency = str(row.get("currency", "USD")).upper()
            location = str(row.get("state") or row.get("country") or "").strip()
            quantity = str(row.get("quantity", "1"))
            brand = str(row.get("brand", ""))
            model = str(row.get("product_name") or row.get("model") or row.get("model_code") or "")
            price_raw = row.get("price", "")
            price_value = ""
            amount = None
            if isinstance(price_raw, (int, float, Decimal)):
                amount = Decimal(str(price_raw))
            elif price_raw is not None:
                price_str = str(price_raw).strip()
                if price_str:
                    match = re.search(r"(\d+(?:[.,]\d+)?)", price_str.replace(" ", ""))
                    if match:
                        candidate = match.group(1).replace(',', '.')
                        try:
                            amount = Decimal(candidate)
                        except InvalidOperation:
                            pass
            if amount is not None:
                normalized = format(amount.normalize(), 'f')
                price_value = normalized.rstrip('0').rstrip('.') if '.' in normalized else normalized
            else:
                price_value = ''.join(ch for ch in str(price_raw) if ch.isdigit())
            details = row.get("description") or f"{row.get('memory','')} {row.get('color','')}".strip()

            # Category (required) with relaxed fallback
            category_el = wait.until(EC.presence_of_element_located((By.NAME, "category")))
            try:
                Select(category_el).select_by_visible_text(category)
            except Exception:
                # Fallback: relaxed match or first non-placeholder
                self._select_relaxed(category_el, [category, "Mobile Phones", "Phones", "Mobiles"]) or (
                    Select(category_el).select_by_index(1)
                )
            # Subcategory becomes available after category selection; pick first available
            try:
                subcat_el = None
                for loc in [(By.ID, "subcategory"), (By.NAME, "subcategory")]:
                    try:
                        subcat_el = WebDriverWait(driver, 8).until(EC.presence_of_element_located(loc))
                        break
                    except Exception:
                        continue
                if subcat_el:
                    try:
                        sub_dd = Select(subcat_el)
                        # choose first non-disabled, non-placeholder option
                        idx = 1
                        opts = sub_dd.options
                        for i, o in enumerate(opts):
                            if i == 0:
                                continue
                            if o.get_attribute("disabled"):
                                continue
                            if (o.text or "").strip():
                                idx = i
                                break
                        sub_dd.select_by_index(idx)
                    except Exception:
                        pass
            except Exception:
                pass

            # Condition (required)
            condition_select = Select(driver.find_element(By.NAME, "condition"))
            condition_select.select_by_visible_text(condition)

            # Currency (required)
            currency_select = Select(driver.find_element(By.NAME, "currency"))
            currency_select.select_by_visible_text(currency)

            # Location (optional)
            if location:
                location_field = driver.find_element(By.ID, "location")
                location_field.clear()
                location_field.send_keys(location)

            # Product fields (required)
            qty_field = driver.find_element(By.NAME, "product[1][quantity]")
            qty_field.clear()
            qty_field.send_keys(quantity)

            brand_field = driver.find_element(By.NAME, "product[1][brand]")
            brand_field.clear()
            brand_field.send_keys(brand)

            model_field = driver.find_element(By.NAME, "product[1][model]")
            model_field.clear()
            model_field.send_keys(model)

            price_field = driver.find_element(By.NAME, "product[1][price]")
            price_field.clear()
            if price_value:
                price_field.send_keys(price_value)

            # Details (optional)
            if details:
                details_field = driver.find_element(By.NAME, "product[1][details]")
                details_field.clear()
                details_field.send_keys(str(details)[:150])

            price_display = price_value or str(price_raw or "")
            print(f"✅ Form filled: {brand} {model} x{quantity} @ {price_display} {currency}")
            self._capture_step("kadorf_product_filled", f"{brand} {model} x{quantity} @ {price_display}")
            return True
        except Exception as e:
            print(f"⚠️  Form filling error: {e}")
            return False

    def post_listing(self, row):
        """Post listing to Kadorf - optimized and modularized.

        Fills the sell form using `_fill_kadorf_form` and then submits using
        resilient strategies; returns a high-signal status string."""
        driver = self.driver
        wait = WebDriverWait(driver, 15)  # Reduced timeout for speed
        
        try:
            # Navigate directly to the posting page
            print("📍 Navigating to Kadorf Sell page...")
            driver.get("https://www.kardof.com/sell")
            self._capture_step("kadorf_sell_page", "Opened Kadorf sell page")
            self._dismiss_common_popups(['.cookie', '.modal', '#cookie-banner'])
            
            # Reduced wait for form to load
            time.sleep(1.5)
            
            print("📝 Filling Kadorf listing form (fast mode)...")
            
            # Fill the form using helper
            ok = self._fill_kadorf_form(row, wait)
            if not ok:
                # Continue to try submission anyway
                pass
            
            # Quick submit attempt
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'].y-button, button[type='submit'], input[type='submit']")))
                driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", submit_btn)
                time.sleep(0.1)
                try:
                    driver.execute_script("if(window.setFormSubmitting){try{setFormSubmitting()}catch(e){}}")
                except Exception:
                    pass
                try:
                    submit_btn.click()
                except Exception:
                    # Fallback: submit via form, honoring onsubmit when possible
                    try:
                        form = driver.find_element(By.ID, "postoffer")
                    except Exception:
                        form = None
                    if form:
                        try:
                            driver.execute_script(
                                "if(window.setFormSubmitting){try{setFormSubmitting()}catch(e){}};"
                                "if(arguments[0].requestSubmit){arguments[0].requestSubmit()}else{arguments[0].submit()}",
                                form
                            )
                        except Exception as _:
                            raise
                print("✅ Form submitted via submit button")
                self._capture_step("kadorf_submitted", "Submitted Kadorf offer")
            except Exception:
                try:
                    # Fast fallback: direct form submission
                    form = driver.find_element(By.ID, "postoffer")
                    driver.execute_script(
                        "if(window.setFormSubmitting){try{setFormSubmitting()}catch(e){}};"
                        "if(arguments[0].reportValidity && !arguments[0].reportValidity()){return false;}"
                        "if(arguments[0].requestSubmit){arguments[0].requestSubmit()}else{arguments[0].submit()}",
                        form
                    )
                    print("✅ Form submitted via JavaScript")
                    self._capture_step("kadorf_form_submitted", "Submitted via form JS")
                except Exception as e:
                    print(f"❌ Submit failed: {e}")
                    return "Error: Could not submit Kadorf form"
            
            # Quick response check (reduced wait)
            time.sleep(2)
            page_text = driver.page_source.lower()
            
            if any(keyword in page_text for keyword in ["success", "thank you", "submitted", "offer posted"]):
                print("🎉 Kadorf posting successful")
                self._capture_step("kadorf_success", "Kadorf offer posted successfully")
                return "Success: Kadorf offer posted"
            elif any(keyword in page_text for keyword in ["error", "required", "invalid", "please fill"]):
                print("❌ Kadorf form errors detected")
                self._capture_step("kadorf_error", "Form submission error")
                return "Error: Form submission failed - check required fields"
            else:
                print("⏳ Kadorf posting pending")
                return "Pending: Submitted offer; waiting for confirmation"
            
        except TimeoutException as e:
            print(f"⏰ Kadorf timeout: {e}")
            return "Timeout posting listing"
        except Exception as e:
            print(f"❌ Kadorf error: {e}")
            self._capture_step("kadorf_exception", str(e))
            return f"Error: {str(e)}"


# Register
ENHANCED_POSTERS['kardof'] = EnhancedKardofPoster


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
    # Smoke tests: GSM Exchange login and Kadorf page open
    test_platform_login_with_2fa('gsmexchange')
    try:
        print("\n🧪 Smoke: open Kadorf Sell page")
        opts = webdriver.ChromeOptions(); opts.add_argument("--window-size=1920,1080")
        drv = webdriver.Chrome(options=opts)
        poster = EnhancedKardofPoster(drv)
        drv.get("https://www.kardof.com/sell"); time.sleep(1.5)
        poster._capture_step("kadorf_sell_smoke", "Opened Kadorf sell page for smoke test")
    except Exception as e:
        print(f"⚠️  Kadorf smoke open error: {e}")
    finally:
        try:
            drv.quit()
        except Exception:
            pass
