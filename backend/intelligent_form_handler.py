#!/usr/bin/env python3
"""
Intelligent Form Handler with AI Vision
Uses GPT-4o to analyze pages and make decisions on the fly
"""

import os
import base64
import json
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time

class IntelligentFormHandler:
    """AI-powered form handler that can adapt to any page"""
    
    def __init__(self, driver: webdriver.Chrome, openai_key: str = None):
        self.driver = driver
        self.client = OpenAI(api_key=openai_key or os.getenv("OPENAI_API_KEY"))
        self.wait = WebDriverWait(driver, 10)
        
    def take_screenshot_base64(self) -> str:
        """Take screenshot and return as base64"""
        screenshot = self.driver.get_screenshot_as_png()
        return base64.b64encode(screenshot).decode('utf-8')
    
    def get_page_structure(self) -> Dict:
        """Extract page structure including forms, inputs, dropdowns"""
        structure = self.driver.execute_script("""
            function getPageStructure() {
                const forms = document.querySelectorAll('form');
                const structure = {
                    forms: [],
                    url: window.location.href,
                    title: document.title
                };
                
                forms.forEach((form, formIndex) => {
                    const formData = {
                        index: formIndex,
                        id: form.id,
                        class: form.className,
                        inputs: [],
                        selects: [],
                        textareas: [],
                        buttons: []
                    };
                    
                    // Get all inputs
                    form.querySelectorAll('input').forEach(input => {
                        formData.inputs.push({
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            value: input.value,
                            placeholder: input.placeholder,
                            required: input.required,
                            visible: input.offsetParent !== null
                        });
                    });
                    
                    // Get all selects (dropdowns)
                    form.querySelectorAll('select').forEach(select => {
                        const options = [];
                        select.querySelectorAll('option').forEach(opt => {
                            options.push({
                                value: opt.value,
                                text: opt.text,
                                selected: opt.selected
                            });
                        });
                        
                        formData.selects.push({
                            name: select.name,
                            id: select.id,
                            options: options,
                            required: select.required,
                            visible: select.offsetParent !== null
                        });
                    });
                    
                    // Get all textareas
                    form.querySelectorAll('textarea').forEach(textarea => {
                        formData.textareas.push({
                            name: textarea.name,
                            id: textarea.id,
                            value: textarea.value,
                            placeholder: textarea.placeholder,
                            required: textarea.required,
                            visible: textarea.offsetParent !== null
                        });
                    });
                    
                    // Get submit buttons
                    form.querySelectorAll('input[type="submit"], button[type="submit"]').forEach(btn => {
                        formData.buttons.push({
                            type: btn.type,
                            value: btn.value || btn.textContent,
                            visible: btn.offsetParent !== null
                        });
                    });
                    
                    structure.forms.push(formData);
                });
                
                return structure;
            }
            
            return getPageStructure();
        """)
        
        return structure
    
    def ask_ai_for_guidance(self, task: str, page_structure: Dict, screenshot_b64: str, 
                           user_data: Dict) -> Dict:
        """Ask GPT-4o what to do next based on screenshot and page structure"""
        
        prompt = f"""You are an expert web automation assistant. Analyze the current page and provide specific instructions.

TASK: {task}

USER DATA TO FILL:
{json.dumps(user_data, indent=2)}

PAGE STRUCTURE:
{json.dumps(page_structure, indent=2)}

Based on the screenshot and page structure, provide a JSON response with:
1. Which form to use (form index)
2. Exactly what to fill in each field
3. Which dropdown options to select
4. Any special instructions

Response format:
{{
    "form_index": 0,
    "actions": [
        {{
            "type": "fill_input",
            "field_name": "txtBrandModel",
            "value": "Apple iPhone 14 Pro"
        }},
        {{
            "type": "select_dropdown",
            "field_name": "selCondition",
            "select_by": "text",
            "value": "New"
        }}
    ],
    "submit_button_index": 0,
    "special_notes": "any special handling needed"
}}
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
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
            max_tokens=1000,
            temperature=0.3
        )
        
        try:
            content = response.choices[0].message.content
            print(f"🤖 AI Raw Response: {content[:500]}...")  # Debug print
            
            # Try to extract JSON from the response
            if "```json" in content:
                # Extract JSON from markdown code block
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    content = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                # Try to extract JSON object
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                content = content[json_start:json_end]
                
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"📄 Full response: {response.choices[0].message.content}")
            # Return a default response
            return {
                "form_index": 0,
                "actions": [],
                "special_notes": "AI response was not valid JSON"
            }
    
    def execute_ai_instructions(self, instructions: Dict) -> bool:
        """Execute the instructions from AI"""
        try:
            form_index = instructions.get("form_index", 0)
            
            # Get the specific form
            form = self.driver.execute_script(f"return document.querySelectorAll('form')[{form_index}];")
            
            if not form:
                print(f"❌ Form at index {form_index} not found")
                return False
            
            # Execute each action
            for action in instructions.get("actions", []):
                action_type = action.get("type")
                field_name = action.get("field_name")
                value = action.get("value")
                
                print(f"🤖 Executing: {action_type} on {field_name}")
                
                if action_type == "fill_input":
                    self.driver.execute_script(f"""
                        var form = document.querySelectorAll('form')[{form_index}];
                        var field = form.querySelector('[name="{field_name}"]');
                        if (field) {{
                            field.value = "{value}";
                            field.dispatchEvent(new Event('change'));
                            console.log('Filled {field_name} with {value}');
                        }}
                    """)
                    
                elif action_type == "select_dropdown":
                    select_by = action.get("select_by", "text")
                    self.driver.execute_script(f"""
                        var form = document.querySelectorAll('form')[{form_index}];
                        var select = form.querySelector('select[name="{field_name}"]');
                        if (select) {{
                            var options = select.querySelectorAll('option');
                            for (var i = 0; i < options.length; i++) {{
                                if ({select_by == 'text' and f'options[i].text.includes("{value}")' or f'options[i].value == "{value}"'}) {{
                                    select.value = options[i].value;
                                    select.dispatchEvent(new Event('change'));
                                    console.log('Selected {value} in {field_name}');
                                    break;
                                }}
                            }}
                        }}
                    """)
                    
                elif action_type == "fill_textarea":
                    self.driver.execute_script(f"""
                        var form = document.querySelectorAll('form')[{form_index}];
                        var textarea = form.querySelector('textarea[name="{field_name}"]');
                        if (textarea) {{
                            textarea.value = `{value}`;
                            textarea.dispatchEvent(new Event('change'));
                            console.log('Filled textarea {field_name}');
                        }}
                    """)
                
                time.sleep(0.5)  # Small delay between actions
            
            return True
            
        except Exception as e:
            print(f"❌ Error executing instructions: {e}")
            return False
    
    def handle_form_intelligently(self, task: str, user_data: Dict) -> Tuple[bool, str]:
        """Main method to handle any form intelligently"""
        try:
            print(f"\n🧠 AI FORM HANDLER: {task}")
            
            # Step 1: Take screenshot
            print("📸 Taking screenshot...")
            screenshot = self.take_screenshot_base64()
            
            # Step 2: Get page structure
            print("🔍 Analyzing page structure...")
            structure = self.get_page_structure()
            print(f"📋 Found {len(structure['forms'])} forms on page")
            
            # Step 3: Ask AI for guidance
            print("🤖 Asking AI for guidance...")
            instructions = self.ask_ai_for_guidance(task, structure, screenshot, user_data)
            print(f"💡 AI Instructions: {json.dumps(instructions, indent=2)}")
            
            # Step 4: Execute instructions
            print("⚡ Executing AI instructions...")
            success = self.execute_ai_instructions(instructions)
            
            if success:
                print("✅ Instructions executed successfully")
                
                # Step 5: Submit if instructed
                if "submit_button_index" in instructions:
                    print("📤 Submitting form...")
                    self.driver.execute_script(f"""
                        var form = document.querySelectorAll('form')[{instructions['form_index']}];
                        var buttons = form.querySelectorAll('input[type="submit"], button[type="submit"]');
                        if (buttons[{instructions['submit_button_index']}]) {{
                            buttons[{instructions['submit_button_index']}].click();
                            console.log('Form submitted');
                        }}
                    """)
                    
                    time.sleep(5)  # Wait for submission
                    
                    # Take final screenshot
                    final_screenshot = self.take_screenshot_base64()
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"ai_form_result_{timestamp}.png"
                    
                    with open(screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(final_screenshot))
                    
                    print(f"📸 Final screenshot saved: {screenshot_path}")
                
                return True, "Form handled successfully"
            else:
                return False, "Failed to execute AI instructions"
                
        except Exception as e:
            print(f"❌ Error in intelligent handler: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def handle_unexpected_situation(self, error_description: str) -> Dict:
        """Handle unexpected situations by asking AI what to do"""
        print(f"\n🚨 UNEXPECTED SITUATION: {error_description}")
        
        screenshot = self.take_screenshot_base64()
        structure = self.get_page_structure()
        
        prompt = f"""An unexpected situation occurred during web automation:

ERROR: {error_description}

PAGE URL: {structure.get('url', 'Unknown')}
PAGE STRUCTURE: {json.dumps(structure, indent=2)}

Analyze the screenshot and provide guidance on how to proceed. 
What should we click or do next to resolve this issue?

Provide a JSON response with specific actions to take.
"""
        
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
                                "url": f"data:image/png;base64,{screenshot}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        try:
            content = response.choices[0].message.content
            print(f"🤖 AI Raw Response: {content[:500]}...")  # Debug print
            
            # Try to extract JSON from the response
            if "```json" in content:
                # Extract JSON from markdown code block
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    content = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                # Try to extract JSON object
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                content = content[json_start:json_end]
                
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"📄 Full response: {response.choices[0].message.content}")
            # Return a default response
            return {
                "form_index": 0,
                "actions": [],
                "special_notes": "AI response was not valid JSON"
            }