#!/usr/bin/env python3
"""
AI Page Analyzer - Uses GPT-4o Mini to analyze the page
"""

import os
import base64
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
import json

class CellpexAIAnalyzer:
    """Uses GPT-4o Mini to analyze Cellpex pages"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def analyze_submit_button(self):
        """Use AI to find the submit button"""
        
        # Take screenshot
        screenshot = self.driver.get_screenshot_as_png()
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        # Get page HTML structure
        page_html = self.driver.execute_script("""
            // Get all visible buttons and inputs
            var elements = [];
            
            // Find all potential submit elements
            var candidates = document.querySelectorAll(
                'input[type="submit"], input[type="button"], button'
            );
            
            candidates.forEach(function(el) {
                if (el.offsetParent !== null) {  // Is visible
                    elements.push({
                        tag: el.tagName,
                        type: el.type,
                        value: el.value || el.innerText,
                        id: el.id,
                        name: el.name,
                        class: el.className,
                        onclick: el.onclick ? 'has onclick' : 'no onclick'
                    });
                }
            });
            
            return elements;
        """)
        
        # Ask GPT-4o Mini to analyze
        prompt = f"""You are analyzing a Cellpex inventory listing form. 
        
The user has filled out all the fields for posting a wholesale inventory listing.
Now they need to submit the form.

Here are all the visible buttons/inputs on the page:
{json.dumps(page_html, indent=2)}

Based on the screenshot and button information, which element is most likely the submit button for posting the inventory listing?

Important: This is the LISTING form, not a search form. Look for buttons with text like:
- Save
- Submit
- Post
- List Item
- Add Listing
- Create Listing

Respond with a JSON object:
{{
    "found": true/false,
    "selector": "CSS selector to use",
    "reasoning": "why you chose this button"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse response
            content = response.choices[0].message.content
            print(f"🤖 AI Analysis: {content}")
            
            # Extract JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"❌ AI Analysis error: {e}")
            return {"found": False, "selector": None, "reasoning": "AI analysis failed"}
    
    def find_and_click_submit(self):
        """Use AI to find and click the submit button"""
        
        analysis = self.analyze_submit_button()
        
        if analysis.get("found") and analysis.get("selector"):
            print(f"🤖 AI found submit button: {analysis['selector']}")
            print(f"📝 Reasoning: {analysis['reasoning']}")
            
            try:
                # Try to click the button
                button = self.driver.find_element(By.CSS_SELECTOR, analysis['selector'])
                
                # Highlight it
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid green';
                    arguments[0].style.backgroundColor = 'yellow';
                """, button)
                
                # Screenshot
                self.driver.save_screenshot("ai_found_submit_button.png")
                
                # Click it
                button.click()
                print("✅ AI successfully clicked submit button!")
                return True
                
            except Exception as e:
                print(f"❌ Could not click AI-suggested button: {e}")
                return False
        else:
            print("❌ AI could not find submit button")
            return False