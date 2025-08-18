#!/usr/bin/env python3
"""
Vision Navigator

Upgraded AI navigation from o4-mini-high to GPT-5 with medium reasoning capability.
Provides screenshot-driven, honest analysis of web pages during automation.
"""

import os
import base64
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openai import OpenAI
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


class GPT5VisionNavigator:
    """
    Uses GPT-5 for vision-based web navigation and form analysis.
    Configured for medium reasoning for a balance of speed and accuracy.
    """
    
    def __init__(self, api_key: Optional[str] = None, verbose: bool = True):
        """Initialize the navigator with OpenAI API"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.verbose = verbose
        self.context_history: List[Dict[str, Any]] = []
        self.screenshot_count = 0
        
    def take_screenshot(self, driver: WebDriver, description: str = "") -> str:
        """Take and encode screenshot as base64"""
        self.screenshot_count += 1
        screenshot = driver.get_screenshot_as_base64()
        
        if self.verbose:
            print(f"📸 Screenshot #{self.screenshot_count}: {description}")
            # Save screenshot for debugging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_{self.screenshot_count}.png"
            with open(filename, "wb") as f:
                f.write(base64.b64decode(screenshot))
            print(f"💾 Saved as: {filename}")
        
        return screenshot
    
    def get_page_context(self, driver: WebDriver) -> Dict[str, Any]:
        """Extract comprehensive page context"""
        context = {
            "url": driver.current_url,
            "title": driver.title,
            "timestamp": datetime.now().isoformat()
        }
        
        # Try to get form elements
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            context["form_count"] = len(forms)
            
            # Get visible input fields
            inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea")
            context["visible_inputs"] = len(inputs)
            
            # Check for error messages
            error_selectors = [
                ".error", ".has-error", ".validation-error", 
                "[class*='error']", "[class*='invalid']"
            ]
            errors = []
            for selector in error_selectors:
                error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                errors.extend([e.text for e in error_elements if e.text])
            context["errors"] = errors[:5]  # Limit to 5 errors
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error extracting page context: {e}")
        
        return context
    
    def analyze_screenshot(
        self, 
        driver: WebDriver, 
        task: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze screenshot with GPT-5 (medium reasoning) for honest assessment"""
        # Take screenshot
        screenshot_b64 = self.take_screenshot(driver, task)
        page_context = self.get_page_context(driver)
        
        # Build context from history
        recent_history = "\n".join([
            f"Step {i+1}: {h['task']} -> {h['result']}"
            for i, h in enumerate(self.context_history[-3:])
        ])
        
        # Prepare the prompt - EMPHASIZING HONESTY
        system_prompt = """You are an ACCURATE and HONEST web automation assistant using vision analysis.

YOUR PRIME DIRECTIVE: Tell the truth about what you see. If something failed, say it failed.
Never claim success unless you see explicit success indicators.

When analyzing pages:
1. Look for validation errors, error messages, and failure indicators
2. Check if forms are still visible (usually means submission failed)
3. Look for success messages, confirmations, or redirects
4. Be specific about what elements you can see

Respond in JSON format:
{
    "current_state": "Exact description of what you see",
    "success_indicators": ["List of success signs if any"],
    "failure_indicators": ["List of failure signs if any"],
    "warnings": ["Any warnings or errors visible"],
    "next_action": {
        "type": "click|type|select|scroll|wait|none",
        "selector": "CSS selector or XPath",
        "value": "Value if type/select action",
        "reason": "Why this action"
    },
    "confidence": "high|medium|low",
    "page_analysis": "Detailed analysis of the page state"
}"""

        user_prompt = f"""Task: {task}

Page Context:
- URL: {page_context['url']}
- Title: {page_context['title']}
- Forms on page: {page_context.get('form_count', 0)}
- Visible inputs: {page_context.get('visible_inputs', 0)}
- Errors detected: {page_context.get('errors', [])}

Recent History:
{recent_history}

{f'Additional Context: {additional_context}' if additional_context else ''}

Analyze the screenshot and provide an HONEST assessment. If you see errors or the form is still visible after submission, report it as a failure."""

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                reasoning_effort="medium"
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                # Handle markdown code blocks
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                
                result = json.loads(json_str)
                
                # Add to context history
                self.context_history.append({
                    "task": task,
                    "result": result.get("current_state", "Unknown"),
                    "timestamp": datetime.now().isoformat()
                })
                
                if self.verbose:
                    print(f"\n🧠 O4-Mini-High Analysis:")
                    print(f"  State: {result.get('current_state', 'Unknown')}")
                    if result.get('failure_indicators'):
                        print(f"  ❌ Failures: {result['failure_indicators']}")
                    if result.get('success_indicators'):
                        print(f"  ✅ Success: {result['success_indicators']}")
                    print(f"  Next: {result.get('next_action', {}).get('type', 'none')}")
                    print(f"  Confidence: {result.get('confidence', 'unknown')}")
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse JSON response: {e}")
                print(f"Raw response: {content[:500]}...")
                
                # Return a safe default
                return {
                    "current_state": "Failed to parse AI response",
                    "warnings": ["JSON parsing error"],
                    "next_action": {"type": "none"},
                    "confidence": "low",
                    "page_analysis": content
                }
                
        except Exception as e:
            print(f"❌ AI analysis error: {e}")
            return {
                "current_state": f"AI analysis failed: {str(e)}",
                "warnings": ["AI analysis error"],
                "next_action": {"type": "none"},
                "confidence": "low",
                "page_analysis": ""
            }

    def analyze_image_b64(
        self,
        image_b64: str,
        task: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a pre-captured base64 screenshot with GPT-5 (medium reasoning)."""
        # Build minimal page context (URL/title unknown in this mode)
        page_context = {"url": "", "title": "", "form_count": 0, "visible_inputs": 0, "errors": []}
        recent_history = "\n".join([
            f"Step {i+1}: {h['task']} -> {h['result']}" for i, h in enumerate(self.context_history[-3:])
        ])
        system_prompt = """You are an ACCURATE and HONEST web automation assistant using vision analysis.

YOUR PRIME DIRECTIVE: Tell the truth about what you see. If something failed, say it failed.
Never claim success unless you see explicit success indicators.

When analyzing pages:
1. Look for validation errors, error messages, and failure indicators
2. Check if forms are still visible (usually means submission failed)
3. Look for success messages, confirmations, or redirects
4. Be specific about what elements you can see

Respond in JSON format:
{
    "current_state": "Exact description of what you see",
    "success_indicators": ["List of success signs if any"],
    "failure_indicators": ["List of failure signs if any"],
    "warnings": ["Any warnings or errors visible"],
    "next_action": {"type": "click|type|select|scroll|wait|none", "selector": "CSS selector or XPath", "value": "Value if type/select action", "reason": "Why this action"},
    "confidence": "high|medium|low",
    "page_analysis": "Detailed analysis of the page state"
}"""
        user_prompt = f"""Task: {task}

Page Context:
- URL: {page_context.get('url','')}
- Title: {page_context.get('title','')}
- Forms on page: {page_context.get('form_count', 0)}
- Visible inputs: {page_context.get('visible_inputs', 0)}
- Errors detected: {page_context.get('errors', [])}

Recent History:
{recent_history}

{f'Additional Context: {additional_context}' if additional_context else ''}

Analyze the screenshot and provide an HONEST assessment. If you see errors or the form is still visible after submission, report it as a failure."""
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"}}
                        ]
                    }
                ],
                reasoning_effort="medium"
            )
            content = response.choices[0].message.content
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                result = json.loads(json_str)
                self.context_history.append({
                    "task": task,
                    "result": result.get("current_state", "Unknown"),
                    "timestamp": datetime.now().isoformat()
                })
                return result
            except json.JSONDecodeError:
                return {
                    "current_state": "Failed to parse AI response",
                    "warnings": ["JSON parsing error"],
                    "next_action": {"type": "none"},
                    "confidence": "low",
                    "page_analysis": content
                }
        except Exception as e:
            return {
                "current_state": f"AI analysis failed: {str(e)}",
                "warnings": ["AI analysis error"],
                "next_action": {"type": "none"},
                "confidence": "low",
                "page_analysis": ""
            }
    
    def wait_for_page_change(
        self, 
        driver: WebDriver, 
        timeout: int = 10,
        check_interval: float = 0.5
    ) -> bool:
        """Wait for page to change (URL or significant DOM changes)"""
        initial_url = driver.current_url
        initial_body_text = driver.find_element(By.TAG_NAME, "body").text[:1000]
        
        if self.verbose:
            print(f"⏳ Waiting for page change from: {initial_url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_url = driver.current_url
            try:
                current_body_text = driver.find_element(By.TAG_NAME, "body").text[:1000]
            except:
                current_body_text = ""
            
            # Check if URL changed
            if current_url != initial_url:
                if self.verbose:
                    print(f"✅ Page changed to: {current_url}")
                return True
            
            # Check if content significantly changed
            if abs(len(current_body_text) - len(initial_body_text)) > 100:
                if self.verbose:
                    print(f"✅ Page content changed significantly")
                return True
            
            time.sleep(check_interval)
        
        if self.verbose:
            print(f"⏱️  No significant page change detected after {timeout}s")
        return False
    
    def verify_submission_success(self, driver: WebDriver) -> Tuple[bool, str]:
        """
        Thoroughly verify if a form submission was successful.
        Returns (success: bool, reason: str)
        """
        # Let page settle
        time.sleep(2)
        
        # Analyze current state
        analysis = self.analyze_screenshot(
            driver, 
            "Verify if the submission was successful",
            "Look for success messages, error messages, or if we're still on the form"
        )
        
        # Check for explicit failure indicators
        failures = analysis.get("failure_indicators", [])
        warnings = analysis.get("warnings", [])
        
        if failures or warnings:
            return False, f"Failures detected: {failures + warnings}"
        
        # Check for success indicators
        successes = analysis.get("success_indicators", [])
        if successes:
            return True, f"Success confirmed: {successes}"
        
        # Check if form is still visible
        current_state = analysis.get("current_state", "").lower()
        if any(term in current_state for term in ["form visible", "form still", "on form", "listing form"]):
            return False, "Still on form page - submission likely failed"
        
        # Default to failure if unclear
        return False, "No clear success indicators found"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of navigation session"""
        return {
            "screenshots_taken": self.screenshot_count,
            "steps_completed": len(self.context_history),
            "history": self.context_history
        }


# Test the navigator
if __name__ == "__main__":
    print("🧪 GPT-5 Vision Navigator Test\n")
    
    # Mock test without actual browser
    navigator = GPT5VisionNavigator(verbose=True)
    
    print("✅ Navigator initialized successfully!")
    print(f"📊 Using model: gpt-5 with medium reasoning effort")
    print(f"🎯 Focus: Honest, accurate page analysis without hallucinations")
    
    # Show example analysis structure
    print("\n📋 Example Analysis Output:")
    example = {
        "current_state": "Form visible with validation errors highlighted in red",
        "success_indicators": [],
        "failure_indicators": ["Required fields marked with red", "Error message: 'Please fill all required fields'"],
        "warnings": ["Form submission blocked by validation"],
        "next_action": {
            "type": "type",
            "selector": "#product-name",
            "value": "iPhone 15 Pro",
            "reason": "Fill required product name field"
        },
        "confidence": "high",
        "page_analysis": "The submission form is still visible with multiple validation errors..."
    }
    
    print(json.dumps(example, indent=2))
"""
O4-Mini-High Vision Navigator
Enhanced AI navigation using o4-mini-high reasoning model with vision capabilities
"""

import os
import base64
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openai import OpenAI
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


class O4MiniHighVisionNavigator:
    """
    Uses o4-mini-high model for vision-based web navigation and form filling.
    Provides honest, accurate analysis without hallucinations.
    """
    
    def __init__(self, api_key: Optional[str] = None, verbose: bool = True):
        """Initialize the navigator with OpenAI API"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.verbose = verbose
        self.context_history = []
        self.screenshot_count = 0
        
    def take_screenshot(self, driver: WebDriver, description: str = "") -> str:
        """Take and encode screenshot as base64"""
        self.screenshot_count += 1
        screenshot = driver.get_screenshot_as_base64()
        
        if self.verbose:
            print(f"📸 Screenshot #{self.screenshot_count}: {description}")
            # Save screenshot for debugging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_{self.screenshot_count}.png"
            with open(filename, "wb") as f:
                f.write(base64.b64decode(screenshot))
            print(f"💾 Saved as: {filename}")
        
        return screenshot
    
    def get_page_context(self, driver: WebDriver) -> Dict[str, Any]:
        """Extract comprehensive page context"""
        context = {
            "url": driver.current_url,
            "title": driver.title,
            "timestamp": datetime.now().isoformat()
        }
        
        # Try to get form elements
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            context["form_count"] = len(forms)
            
            # Get visible input fields
            inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea")
            context["visible_inputs"] = len(inputs)
            
            # Check for error messages
            error_selectors = [
                ".error", ".has-error", ".validation-error", 
                "[class*='error']", "[class*='invalid']"
            ]
            errors = []
            for selector in error_selectors:
                error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                errors.extend([e.text for e in error_elements if e.text])
            context["errors"] = errors[:5]  # Limit to 5 errors
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error extracting page context: {e}")
        
        return context
    
    def analyze_screenshot(
        self, 
        driver: WebDriver, 
        task: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot with o4-mini-high for accurate, honest assessment
        """
        # Take screenshot
        screenshot_b64 = self.take_screenshot(driver, task)
        page_context = self.get_page_context(driver)
        
        # Build context from history
        recent_history = "\n".join([
            f"Step {i+1}: {h['task']} -> {h['result']}"
            for i, h in enumerate(self.context_history[-3:])
        ])
        
        # Prepare the prompt - EMPHASIZING HONESTY
        system_prompt = """You are an ACCURATE and HONEST web automation assistant using vision analysis.

YOUR PRIME DIRECTIVE: Tell the truth about what you see. If something failed, say it failed.
Never claim success unless you see explicit success indicators.

When analyzing pages:
1. Look for validation errors, error messages, and failure indicators
2. Check if forms are still visible (usually means submission failed)
3. Look for success messages, confirmations, or redirects
4. Be specific about what elements you can see

Respond in JSON format:
{
    "current_state": "Exact description of what you see",
    "success_indicators": ["List of success signs if any"],
    "failure_indicators": ["List of failure signs if any"],
    "warnings": ["Any warnings or errors visible"],
    "next_action": {
        "type": "click|type|select|scroll|wait|none",
        "selector": "CSS selector or XPath",
        "value": "Value if type/select action",
        "reason": "Why this action"
    },
    "confidence": "high|medium|low",
    "page_analysis": "Detailed analysis of the page state"
}"""

        user_prompt = f"""Task: {task}

Page Context:
- URL: {page_context['url']}
- Title: {page_context['title']}
- Forms on page: {page_context.get('form_count', 0)}
- Visible inputs: {page_context.get('visible_inputs', 0)}
- Errors detected: {page_context.get('errors', [])}

Recent History:
{recent_history}

{f'Additional Context: {additional_context}' if additional_context else ''}

Analyze the screenshot and provide an HONEST assessment. If you see errors or the form is still visible after submission, report it as a failure."""

        try:
            response = self.client.chat.completions.create(
                model="o4-mini-high",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                reasoning_effort="high"  # Maximum reasoning for accuracy
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                # Handle markdown code blocks
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                
                result = json.loads(json_str)
                
                # Add to context history
                self.context_history.append({
                    "task": task,
                    "result": result.get("current_state", "Unknown"),
                    "timestamp": datetime.now().isoformat()
                })
                
                if self.verbose:
                    print(f"\n🧠 O4-Mini-High Analysis:")
                    print(f"  State: {result.get('current_state', 'Unknown')}")
                    if result.get('failure_indicators'):
                        print(f"  ❌ Failures: {result['failure_indicators']}")
                    if result.get('success_indicators'):
                        print(f"  ✅ Success: {result['success_indicators']}")
                    print(f"  Next: {result.get('next_action', {}).get('type', 'none')}")
                    print(f"  Confidence: {result.get('confidence', 'unknown')}")
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse JSON response: {e}")
                print(f"Raw response: {content[:500]}...")
                
                # Return a safe default
                return {
                    "current_state": "Failed to parse AI response",
                    "warnings": ["JSON parsing error"],
                    "next_action": {"type": "none"},
                    "confidence": "low",
                    "page_analysis": content
                }
                
        except Exception as e:
            print(f"❌ AI analysis error: {e}")
            return {
                "current_state": f"AI analysis failed: {str(e)}",
                "warnings": ["AI analysis error"],
                "next_action": {"type": "none"},
                "confidence": "low",
                "page_analysis": ""
            }
    
    def wait_for_page_change(
        self, 
        driver: WebDriver, 
        timeout: int = 10,
        check_interval: float = 0.5
    ) -> bool:
        """Wait for page to change (URL or significant DOM changes)"""
        initial_url = driver.current_url
        initial_body_text = driver.find_element(By.TAG_NAME, "body").text[:1000]
        
        if self.verbose:
            print(f"⏳ Waiting for page change from: {initial_url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_url = driver.current_url
            try:
                current_body_text = driver.find_element(By.TAG_NAME, "body").text[:1000]
            except:
                current_body_text = ""
            
            # Check if URL changed
            if current_url != initial_url:
                if self.verbose:
                    print(f"✅ Page changed to: {current_url}")
                return True
            
            # Check if content significantly changed
            if abs(len(current_body_text) - len(initial_body_text)) > 100:
                if self.verbose:
                    print(f"✅ Page content changed significantly")
                return True
            
            time.sleep(check_interval)
        
        if self.verbose:
            print(f"⏱️  No significant page change detected after {timeout}s")
        return False
    
    def verify_submission_success(self, driver: WebDriver) -> Tuple[bool, str]:
        """
        Thoroughly verify if a form submission was successful.
        Returns (success: bool, reason: str)
        """
        # Let page settle
        time.sleep(2)
        
        # Analyze current state
        analysis = self.analyze_screenshot(
            driver, 
            "Verify if the submission was successful",
            "Look for success messages, error messages, or if we're still on the form"
        )
        
        # Check for explicit failure indicators
        failures = analysis.get("failure_indicators", [])
        warnings = analysis.get("warnings", [])
        
        if failures or warnings:
            return False, f"Failures detected: {failures + warnings}"
        
        # Check for success indicators
        successes = analysis.get("success_indicators", [])
        if successes:
            return True, f"Success confirmed: {successes}"
        
        # Check if form is still visible
        current_state = analysis.get("current_state", "").lower()
        if any(term in current_state for term in ["form visible", "form still", "on form", "listing form"]):
            return False, "Still on form page - submission likely failed"
        
        # Default to failure if unclear
        return False, "No clear success indicators found"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of navigation session"""
        return {
            "screenshots_taken": self.screenshot_count,
            "steps_completed": len(self.context_history),
            "history": self.context_history
        }


# Test the navigator
if __name__ == "__main__":
    print("🧪 O4-Mini-High Vision Navigator Test\n")
    
    # Mock test without actual browser
    navigator = O4MiniHighVisionNavigator(verbose=True)
    
    print("✅ Navigator initialized successfully!")
    print(f"📊 Using model: o4-mini-high with high reasoning effort")
    print(f"🎯 Focus: Honest, accurate page analysis without hallucinations")
    
    # Show example analysis structure
    print("\n📋 Example Analysis Output:")
    example = {
        "current_state": "Form visible with validation errors highlighted in red",
        "success_indicators": [],
        "failure_indicators": ["Required fields marked with red", "Error message: 'Please fill all required fields'"],
        "warnings": ["Form submission blocked by validation"],
        "next_action": {
            "type": "type",
            "selector": "#product-name",
            "value": "iPhone 15 Pro",
            "reason": "Fill required product name field"
        },
        "confidence": "high",
        "page_analysis": "The submission form is still visible with multiple validation errors..."
    }
    
    print(json.dumps(example, indent=2))