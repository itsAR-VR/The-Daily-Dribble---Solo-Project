#!/usr/bin/env python3
"""
Enhanced platform poster with Gmail 2FA integration
"""

import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import Gmail service for 2FA
try:
    from gmail_service import gmail_service
    GMAIL_AVAILABLE = gmail_service and gmail_service.is_available()
except:
    GMAIL_AVAILABLE = False
    gmail_service = None

class Enhanced2FAMarketplacePoster:
    """Enhanced base class with 2FA support via Gmail"""
    
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.driver = driver
        self.username, self.password = self._load_credentials()
        self.gmail_service = gmail_service if GMAIL_AVAILABLE else None
        self.max_2fa_attempts = 3
        self.tfa_wait_time = 30  # seconds to wait for 2FA code
    
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
            
            # Submit login
            submit = driver.find_element(
                By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], button:contains('Login'), button:contains('Sign in')"
            )
            submit.click()
            
            # Check for 2FA
            if self._check_for_2fa():
                print(f"📱 2FA required for {self.PLATFORM}")
                return self._handle_2fa()
            else:
                print(f"✅ Logged into {self.PLATFORM} successfully (no 2FA)")
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
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise code extractor. Return only the authentication code or 'NO_CODE_FOUND'."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0
            )
            
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
            
            # Submit login using the submit input
            submit = wait.until(EC.element_to_be_clickable(
                (By.NAME, "btnLogin")
            ))
            submit.click()
            
            # Wait a bit for potential redirect
            time.sleep(3)
            
            # Check if we're on 2FA page (check URL)
            current_url = driver.current_url
            if "login_verify" in current_url:
                print(f"📱 2FA required for {self.PLATFORM}")
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
    
    def post_listing(self, row):
        """Post listing to Cellpex"""
        driver = self.driver
        wait = WebDriverWait(driver, 20)
        
        try:
            # Navigate to add listing
            driver.get("https://www.cellpex.com/seller/products/create")
            
            # Product details
            # Category selection might be needed
            
            # Product name
            name_field = wait.until(EC.presence_of_element_located(
                (By.NAME, "name")
            ))
            name_field.clear()
            name_field.send_keys(str(row.get("product_name", "")))
            
            # Other fields...
            # Implementation depends on actual Cellpex form structure
            
            return "Success"
            
        except Exception as e:
            return f"Error: {str(e)}"


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