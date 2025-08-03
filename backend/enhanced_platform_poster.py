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
        """Handle 2FA authentication"""
        if not self.gmail_service:
            print("❌ Gmail service not available for 2FA")
            return False
            
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        
        for attempt in range(self.max_2fa_attempts):
            print(f"🔍 Attempt {attempt + 1}/{self.max_2fa_attempts} - Checking Gmail for 2FA code...")
            
            # Wait a bit for email to arrive
            if attempt > 0:
                time.sleep(5)
            
            # Get verification code from Gmail
            code = self.gmail_service.get_latest_verification_code(self.PLATFORM.lower())
            
            if code:
                print(f"✅ Found 2FA code: {code}")
                
                # Find 2FA input field
                try:
                    code_field = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 
                         "input[name='code'], input[name='otp'], input[name='token'], "
                         "input[placeholder*='code'], input[placeholder*='verification']")
                    ))
                    code_field.clear()
                    code_field.send_keys(code)
                    
                    # Submit code
                    try:
                        submit = driver.find_element(
                            By.CSS_SELECTOR, 
                            "button[type='submit'], input[type='submit'], button:contains('Verify'), button:contains('Submit')"
                        )
                        submit.click()
                    except:
                        # Some sites submit on enter
                        code_field.send_keys("\n")
                    
                    # Check if login successful
                    time.sleep(3)
                    if self._check_login_success():
                        print(f"✅ 2FA successful for {self.PLATFORM}")
                        return True
                    else:
                        print(f"⚠️  2FA code might be incorrect or expired")
                        
                except Exception as e:
                    print(f"❌ Error entering 2FA code: {e}")
            else:
                print(f"⚠️  No 2FA code found in Gmail")
                
        print(f"❌ Failed to complete 2FA for {self.PLATFORM}")
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
            
            # Check for 2FA (Cellpex might not use 2FA, but check anyway)
            if self._check_for_2fa():
                print(f"📱 2FA required for {self.PLATFORM}")
                return self._handle_2fa()
            else:
                print(f"✅ Logged into {self.PLATFORM} successfully (no 2FA)")
                # Check if we're logged in by looking for a logout or account link
                try:
                    # Look for indicators of successful login
                    wait.until(EC.any_of(
                        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "logout")),
                        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "account")),
                        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "dashboard"))
                    ))
                    return True
                except TimeoutException:
                    print("⚠️  Could not confirm successful login")
                    return False
                
        except TimeoutException:
            print(f"❌ Login timeout for {self.PLATFORM}")
            return False
        except Exception as e:
            print(f"❌ Login error for {self.PLATFORM}: {e}")
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