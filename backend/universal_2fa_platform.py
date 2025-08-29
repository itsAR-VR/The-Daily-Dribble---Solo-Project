#!/usr/bin/env python3
"""
Universal 2FA Platform Handler - Repeatable architecture for any platform
"""

import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# Import the enhanced base class
from enhanced_platform_poster import Enhanced2FAMarketplacePoster

class Universal2FAPlatform(Enhanced2FAMarketplacePoster):
    """Universal platform handler that works with any platform using the repeatable 2FA architecture"""
    
    def __init__(self, driver: webdriver.Chrome, platform_name: str, login_url: str, login_selectors: dict = None):
        """
        Initialize universal platform handler
        
        Args:
            driver: Selenium Chrome driver
            platform_name: Name of platform (e.g., 'cellpex', 'gsmexchange')
            login_url: Login page URL
            login_selectors: Custom selectors for login form (optional)
        """
        self.PLATFORM = platform_name.upper()
        self.LOGIN_URL = login_url
        self.login_selectors = login_selectors or {}
        
        super().__init__(driver)
    
    def login_with_2fa(self) -> bool:
        """Universal login with 2FA support that works for any platform"""
        driver = self.driver
        driver.get(self.LOGIN_URL)
        wait = WebDriverWait(driver, 20)
        
        try:
            print(f"🔐 Logging into {self.PLATFORM}...")
            
            # Find username field using custom selectors or common patterns
            username_selectors = self.login_selectors.get('username', [
                "input[name='username']",
                "input[name='email']", 
                "input[name='user']",
                "input[name='txtUser']",  # Cellpex style
                "input[type='email']",
                "input[placeholder*='username']",
                "input[placeholder*='email']",
                "#username",
                "#email",
                ".username",
                ".email"
            ])
            
            user_field = self._find_element_by_selectors(wait, username_selectors, "username field")
            if not user_field:
                return False
                
            user_field.clear()
            user_field.send_keys(self.username)
            print(f"✅ Entered username: {self.username}")
            
            # Find password field
            password_selectors = self.login_selectors.get('password', [
                "input[name='password']",
                "input[name='pass']",
                "input[name='txtPass']",  # Cellpex style
                "input[type='password']",
                "input[placeholder*='password']",
                "#password",
                ".password"
            ])
            
            pass_field = self._find_element_by_selectors(wait, password_selectors, "password field")
            if not pass_field:
                return False
                
            pass_field.clear()
            pass_field.send_keys(self.password)
            print(f"✅ Entered password")
            
            # Find submit button
            submit_selectors = self.login_selectors.get('submit', [
                "button[type='submit']",
                "input[type='submit']",
                "input[name='btnLogin']",  # Cellpex style
                "#login",
                ".login",
                "[onclick*='login']"
            ])
            
            submit = self._find_element_by_selectors(wait, submit_selectors, "submit button", clickable=True)
            if not submit:
                # XPath text fallbacks for common login labels to avoid CSS :contains
                for xp in [
                    "//button[contains(.,'Login') or contains(.,'Sign in') or contains(.,'Log in')]",
                    "//input[@type='submit']"
                ]:
                    try:
                        submit = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                        break
                    except Exception:
                        continue
            if not submit:
                return False

            submit.click()
            print(f"✅ Submitted login form")
            
            # Wait for page response
            time.sleep(3)
            
            # Check for 2FA requirement
            if self._check_for_2fa():
                print(f"📱 2FA required for {self.PLATFORM}")
                return self._handle_2fa()
            else:
                # Check if login was successful without 2FA
                if self._check_login_success():
                    print(f"✅ Logged into {self.PLATFORM} successfully (no 2FA)")
                    return True
                else:
                    print(f"⚠️  Login may have failed - checking for errors...")
                    # Could add error message detection here
                    return False
                
        except TimeoutException:
            print(f"❌ Login timeout for {self.PLATFORM}")
            return False
        except Exception as e:
            print(f"❌ Login error for {self.PLATFORM}: {e}")
            return False
    
    def _find_element_by_selectors(self, wait: WebDriverWait, selectors: list, element_name: str, clickable: bool = False) -> object:
        """Try multiple selectors to find an element"""
        for selector in selectors:
            try:
                if clickable:
                    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                else:
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"✅ Found {element_name} using selector: {selector}")
                return element
            except:
                continue
        
        print(f"❌ Could not find {element_name} with any selector")
        return None


def create_platform_handler(platform_name: str, login_url: str, custom_selectors: dict = None) -> Universal2FAPlatform:
    """
    Factory function to create a platform handler for any platform
    
    Args:
        platform_name: Name of the platform (e.g., 'cellpex', 'gsmexchange')
        login_url: Login page URL
        custom_selectors: Optional custom CSS selectors if defaults don't work
    
    Returns:
        Universal2FAPlatform instance ready for 2FA automation
    """
    # Create Chrome driver with automation-friendly options
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920x1080")
    # Keep visible for debugging (remove in production)
    # options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    
    return Universal2FAPlatform(driver, platform_name, login_url, custom_selectors)


# Platform configurations for quick setup
PLATFORM_CONFIGS = {
    'cellpex': {
        'login_url': 'https://www.cellpex.com/login',
        'selectors': {
            'username': ['input[name="txtUser"]'],
            'password': ['input[name="txtPass"]'],
            'submit': ['input[name="btnLogin"]']
        }
    },
    'gsmexchange': {
        'login_url': 'https://www.gsmexchange.com/signin',
        'selectors': {
            'username': ['input[name="username"]', 'input[name="email"]'],
            'password': ['input[name="password"]'],
            'submit': ['button[type="submit"]', 'input[type="submit"]']
        }
    },
    'hubx': {
        'login_url': 'https://app.hubx.com/login',
        'selectors': {
            'username': ['input[name="email"]', 'input[type="email"]'],
            'password': ['input[name="password"]'],
            'submit': ['button[type="submit"]']
        }
    },
    'kardof': {
        'login_url': 'https://www.kardof.com/login',
        'selectors': {
            'username': ['input[name="username"]', 'input[name="email"]'],
            'password': ['input[name="password"]'],
            'submit': ['button[type="submit"]']
        }
    },
    'handlot': {
        'login_url': 'https://www.handlot.com/login',
        'selectors': {
            'username': ['input[name="username"]', 'input[name="email"]'],
            'password': ['input[name="password"]'],
            'submit': ['button[type="submit"]']
        }
    }
}


def quick_platform_setup(platform_name: str) -> Universal2FAPlatform:
    """Quick setup for known platforms"""
    platform_name = platform_name.lower()
    
    if platform_name not in PLATFORM_CONFIGS:
        raise ValueError(f"Platform '{platform_name}' not configured. Use create_platform_handler() for custom platforms.")
    
    config = PLATFORM_CONFIGS[platform_name]
    return create_platform_handler(
        platform_name=platform_name,
        login_url=config['login_url'],
        custom_selectors=config['selectors']
    )


def test_universal_2fa(platform_name: str):
    """Test the universal 2FA flow for any platform"""
    print(f"🚀 Testing Universal 2FA for {platform_name.upper()}...")
    
    try:
        # Create platform handler
        platform = quick_platform_setup(platform_name)
        
        # Test login with 2FA
        success = platform.login_with_2fa()
        
        if success:
            print(f"✅ Successfully completed 2FA login for {platform_name}!")
            # Take screenshot for verification
            platform.driver.save_screenshot(f"{platform_name}_2fa_success.png")
        else:
            print(f"❌ 2FA login failed for {platform_name}")
            platform.driver.save_screenshot(f"{platform_name}_2fa_failed.png")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing {platform_name}: {e}")
        return False
    finally:
        # Always clean up
        if 'platform' in locals():
            platform.driver.quit()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        platform = sys.argv[1]
        test_universal_2fa(platform)
    else:
        print("Usage: python universal_2fa_platform.py <platform_name>")
        print("Available platforms:", list(PLATFORM_CONFIGS.keys()))