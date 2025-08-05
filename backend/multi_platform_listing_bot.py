#!/usr/bin/env python3
"""Multi-platform listing bot.

This script automates posting product listings across multiple wholesale
marketplaces. It reads an Excel spreadsheet describing listings and posts
rows to the appropriate platform using Selenium. The workbook is updated
with success or error messages in a ``Status`` column.

Platforms supported (via subclasses of :class:`MarketplacePoster`):     
    - Hubx
    - GSMExchange
    - Kardof
    - Cellpex
    - Handlot
    - LinkedIn

Each platform expects ``<PLATFORM>_USERNAME`` and ``<PLATFORM>_PASSWORD``
environment variables (e.g. ``HUBX_USERNAME``).

Usage
-----
    python multi_platform_listing_bot.py --input listings.xlsx --output result.xlsx

Dependencies
------------
    pip install selenium pandas openpyxl python-dotenv
"""

from __future__ import annotations

import argparse
import os
from collections import defaultdict
from typing import Dict, List, Type

import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class MarketplacePoster:
    """Base class for marketplace automation."""

    PLATFORM: str = ""
    LOGIN_URL: str = ""

    def __init__(self, driver: webdriver.Chrome) -> None:
        self.driver = driver
        self.username, self.password = self._load_credentials()

    def _load_credentials(self) -> tuple[str, str]:
        load_dotenv()
        user = os.getenv(f"{self.PLATFORM.upper()}_USERNAME")
        pwd = os.getenv(f"{self.PLATFORM.upper()}_PASSWORD")
        if not user or not pwd:
            raise RuntimeError(f"Missing credentials for {self.PLATFORM}")
        return user, pwd

    def login(self) -> None:
        """Login to the marketplace.

        Subclasses should override this method with the steps needed to
        authenticate. The base implementation navigates to ``LOGIN_URL`` and
        fills ``username`` and ``password`` fields using common names.
        """
        if not self.LOGIN_URL:
            raise NotImplementedError("LOGIN_URL must be defined")
        driver = self.driver
        driver.get(self.LOGIN_URL)
        wait = WebDriverWait(driver, 20)
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        pass_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        user_field.clear()
        user_field.send_keys(self.username)
        pass_field.clear()
        pass_field.send_keys(self.password)
        # try common submit button
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit.click()

    def post_listing(self, row: pd.Series) -> str:
        """Post a single listing.

        Parameters
        ----------
        row : pandas.Series
            Row from the spreadsheet.

        Returns
        -------
        str
            ``"Success"`` or an error message.
        """
        raise NotImplementedError


class HubxPoster(MarketplacePoster):
    PLATFORM = "HUBX"
    LOGIN_URL = "https://app.hubx.com/login"

    def post_listing(self, row: pd.Series) -> str:
        # Placeholder implementation. Update selectors as required.
        driver = self.driver
        driver.get("https://app.hubx.com/sell")
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "title"))).send_keys(
                str(row.get("product_name", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "condition"))).send_keys(
                str(row.get("condition", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "quantity"))).send_keys(
                str(row.get("quantity", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "price"))).send_keys(
                str(row.get("price", ""))
            )
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success')]")))
            return "Success"
        except TimeoutException:
            return "Timed out posting listing"
        except Exception as exc:  # pragma: no cover - general error
            return f"Error: {exc}"


class GSMExchangePoster(MarketplacePoster):
    PLATFORM = "GSMEXCHANGE"
    LOGIN_URL = "https://www.gsmexchange.com/login"

    def post_listing(self, row: pd.Series) -> str:
        driver = self.driver
        driver.get("https://www.gsmexchange.com/post")
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "title"))).send_keys(
                str(row.get("product_name", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "condition"))).send_keys(
                str(row.get("condition", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "quantity"))).send_keys(
                str(row.get("quantity", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "price"))).send_keys(
                str(row.get("price", ""))
            )
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success')]")))
            return "Success"
        except TimeoutException:
            return "Timed out posting listing"
        except Exception as exc:  # pragma: no cover - general error
            return f"Error: {exc}"


class KardofPoster(MarketplacePoster):
    PLATFORM = "KARDOF"
    LOGIN_URL = "https://www.kardof.com/login"

    def post_listing(self, row: pd.Series) -> str:
        driver = self.driver
        driver.get("https://www.kardof.com/sell")
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "title"))).send_keys(
                str(row.get("product_name", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "condition"))).send_keys(
                str(row.get("condition", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "quantity"))).send_keys(
                str(row.get("quantity", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "price"))).send_keys(
                str(row.get("price", ""))
            )
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success')]")))
            return "Success"
        except TimeoutException:
            return "Timed out posting listing"
        except Exception as exc:
            return f"Error: {exc}"


class CellpexPoster(MarketplacePoster):
    PLATFORM = "CELLPEX"
    LOGIN_URL = "https://www.cellpex.com/login"

    def post_listing(self, row: pd.Series) -> str:
        driver = self.driver
        driver.get("https://www.cellpex.com/sell")
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "txtProduct"))).send_keys(
                str(row.get("product_name", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "txtCondition"))).send_keys(
                str(row.get("condition", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "txtQty"))).send_keys(
                str(row.get("quantity", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "txtPrice"))).send_keys(
                str(row.get("price", ""))
            )
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Your offer has been posted')]")))
            return "Success"
        except TimeoutException:
            return "Timed out posting listing"
        except Exception as exc:
            return f"Error: {exc}"


class HandlotPoster(MarketplacePoster):
    PLATFORM = "HANDLOT"
    LOGIN_URL = "https://www.handlot.com/login"

    def post_listing(self, row: pd.Series) -> str:
        driver = self.driver
        driver.get("https://www.handlot.com/sell")
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "title"))).send_keys(
                str(row.get("product_name", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "condition"))).send_keys(
                str(row.get("condition", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "quantity"))).send_keys(
                str(row.get("quantity", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "price"))).send_keys(
                str(row.get("price", ""))
            )
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success')]")))
            return "Success"
        except TimeoutException:
            return "Timed out posting listing"
        except Exception as exc:
            return f"Error: {exc}"


class LinkedInPoster(MarketplacePoster):
    PLATFORM = "LINKEDIN"
    LOGIN_URL = "https://www.linkedin.com/login"

    def post_listing(self, row: pd.Series) -> str:
        driver = self.driver
        driver.get("https://www.linkedin.com/sell")  # Placeholder
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "title"))).send_keys(
                str(row.get("product_name", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "condition"))).send_keys(
                str(row.get("condition", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "quantity"))).send_keys(
                str(row.get("quantity", ""))
            )
            wait.until(EC.presence_of_element_located((By.NAME, "price"))).send_keys(
                str(row.get("price", ""))
            )
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success')]")))
            return "Success"
        except TimeoutException:
            return "Timed out posting listing"
        except Exception as exc:
            return f"Error: {exc}"


POSTER_MAP: Dict[str, Type[MarketplacePoster]] = {
    cls.PLATFORM.lower(): cls
    for cls in [
        HubxPoster,
        GSMExchangePoster,
        KardofPoster,
        CellpexPoster,
        HandlotPoster,
        # LinkedInPoster,  # Temporarily disabled
    ]
}


def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    
    # Add headless mode for deployment environments
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("CHROME_BIN"):
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Set user data directory for non-root environments
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR", "/tmp/.chrome")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Set Chrome binary location if specified
    chrome_binary = os.getenv("CHROME_BIN") or os.getenv("CHROME_PATH")
    if chrome_binary:
        options.binary_location = chrome_binary
    
    # Disable automation detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    try:
        # Try to create driver with Service for better error handling
        from selenium.webdriver.chrome.service import Service
        
        # Try to find chromedriver - check environment variables first
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH") or os.getenv("SE_CHROMEDRIVER_PATH")
        
        if not chromedriver_path:
            # Fallback to common locations
            for path in ["/usr/local/bin/chromedriver", "/usr/bin/chromedriver"]:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
        
        # Force disable Selenium Manager
        os.environ['SE_SKIP_DRIVER_DOWNLOAD'] = '1'
        
        # Always use explicit service to avoid Selenium Manager issues
        if chromedriver_path and os.path.exists(chromedriver_path):
            print(f"Using ChromeDriver at: {chromedriver_path}")
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # If path not found but env var is set, use it anyway
            chromedriver_path = chromedriver_path or "/usr/local/bin/chromedriver"
            print(f"Forcing ChromeDriver path: {chromedriver_path}")
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
        return driver
    except Exception as e:
        # More detailed error information
        print(f"Chrome driver creation error: {e}")
        print(f"Chrome binary location: {chrome_path}")
        print(f"PATH: {os.environ.get('PATH', 'Not set')}")
        
        # Check if chrome and chromedriver exist
        import subprocess
        try:
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
            print(f"Chrome location: {result.stdout.strip()}")
        except:
            print("Could not find google-chrome")
            
        try:
            result = subprocess.run(["which", "chromedriver"], capture_output=True, text=True)
            print(f"ChromeDriver location: {result.stdout.strip()}")
        except:
            print("Could not find chromedriver")
            
        raise RuntimeError(f"Failed to create Chrome driver: {e}")


def process_platform(platform: str, rows: pd.DataFrame, driver: webdriver.Chrome) -> pd.DataFrame:
    poster_cls = POSTER_MAP.get(platform.lower())
    if not poster_cls:
        rows.loc[:, "Status"] = f"Unsupported platform: {platform}"
        return rows
    poster = poster_cls(driver)
    try:
        poster.login()
    except Exception as exc:  # pragma: no cover - login failure
        rows.loc[:, "Status"] = f"Login error: {exc}"
        return rows

    for idx, row in rows.iterrows():
        try:
            result = poster.post_listing(row)
        except Exception as exc:  # pragma: no cover - unexpected
            result = f"Unhandled error: {exc}"
        rows.at[idx, "Status"] = result
    return rows


def run_from_spreadsheet(input_path: str, output_path: str) -> None:
    """Process listings from an Excel spreadsheet and save results.
    
    This function can be imported and used by other modules like a FastAPI app.
    
    Parameters
    ----------
    input_path : str
        Path to the input Excel file with listings
    output_path : str
        Path where the results Excel file should be saved
    """
    df = pd.read_excel(input_path)
    if "Status" not in df.columns:
        df["Status"] = ""

    driver = create_driver()
    try:
        grouped = df.groupby(df["platform"].str.lower())
        results: List[pd.DataFrame] = []
        for platform, rows in grouped:
            res = process_platform(platform, rows.copy(), driver)
            results.append(res)
        final_df = pd.concat(results).sort_index()
    finally:
        driver.quit()

    final_df.to_excel(output_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Post listings to multiple marketplaces")
    parser.add_argument("--input", required=True, help="Excel file with listings")
    parser.add_argument("--output", help="Where to save results (default: overwrite input)")
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output or input_path

    run_from_spreadsheet(input_path, output_path)
    print(f"Updated listings written to {output_path}")


if __name__ == "__main__":
    main()
