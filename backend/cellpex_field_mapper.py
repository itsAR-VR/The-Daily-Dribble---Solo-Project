#!/usr/bin/env python3
"""
Cellpex Field Mapper - Maps user input to exact form fields
"""

from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

class CellpexFieldMapper:
    """Maps frontend user data to Cellpex form fields"""
    
    # Field mapping configuration
    FIELD_MAPPINGS = {
        # Dropdowns
        'category': {
            'field_name': 'selCateg',
            'type': 'dropdown',
            'mapping': {
                'Cell Phones': 'cell-phones',
                'Smartphones': 'smartphones',
                'Tablets': 'tablets',
                'Smartwatches': 'smartwatches'
            }
        },
        'brand': {
            'field_name': 'selBrand',
            'type': 'dropdown',
            'mapping': {
                'Apple': 'apple',
                'Samsung': 'samsung',
                'Google': 'google',
                'OnePlus': 'oneplus',
                'Xiaomi': 'xiaomi'
            }
        },
        'condition': {
            'field_name': 'selCondition',
            'type': 'dropdown',
            'mapping': {
                'New': 'new',
                'Like New': 'like-new',
                'Excellent': 'excellent',
                'Good': 'good',
                'Fair': 'fair',
                'Poor': 'poor'
            }
        },
        'sim_lock': {
            'field_name': 'selSIMlock',
            'type': 'dropdown',
            'mapping': {
                'Unlocked': 'unlocked',
                'Locked': 'locked',
                'Factory Unlocked': 'factory-unlocked'
            }
        },
        'market_spec': {
            'field_name': 'selMarketSpec',
            'type': 'dropdown',
            'mapping': {
                'US Market': 'us',
                'EU Market': 'eu',
                'Asian Market': 'asia',
                'Global': 'global'
            }
        },
        'packing': {
            'field_name': 'selPacking',
            'type': 'dropdown',
            'mapping': {
                'Original Box': 'original',
                'Bulk': 'bulk',
                'Refurbished Box': 'refurb',
                'No Box': 'no-box'
            }
        },
        'incoterm': {
            'field_name': 'selIncoterm',
            'type': 'dropdown',
            'mapping': {
                'FOB': 'fob',
                'CIF': 'cif',
                'EXW': 'exw',
                'DDP': 'ddp'
            }
        },
        
        # Text inputs
        'available_date': {
            'field_name': 'txtAvailable',
            'type': 'date'
        },
        'quantity': {
            'field_name': 'txtQuantity',
            'type': 'number'
        },
        'min_order': {
            'field_name': 'txtMinOrder',
            'type': 'number'
        },
        'price': {
            'field_name': 'txtPrice',
            'type': 'number'
        },
        'item_weight': {
            'field_name': 'txtWeight',
            'type': 'number'
        },
        'carrier': {
            'field_name': 'txtCarrier',
            'type': 'text'
        },
        'product_name': {
            'field_name': 'txtBrandModel',
            'type': 'text'
        },
        
        # Textareas
        'description': {
            'field_name': 'areaComments',
            'type': 'textarea'
        },
        'remarks': {
            'field_name': 'areaRemarks',
            'type': 'textarea'
        }
    }
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        
    def map_and_fill_form(self, user_data: Dict) -> Dict[str, bool]:
        """Map user data to form fields and fill them"""
        results = {}
        
        # Fill dropdowns first
        for field, config in self.FIELD_MAPPINGS.items():
            if config['type'] == 'dropdown' and field in user_data:
                success = self._fill_dropdown(
                    config['field_name'],
                    user_data[field],
                    config.get('mapping', {})
                )
                results[field] = success
                
        # Fill text inputs
        for field, config in self.FIELD_MAPPINGS.items():
            if config['type'] in ['text', 'number', 'date'] and field in user_data:
                success = self._fill_input(
                    config['field_name'],
                    user_data[field]
                )
                results[field] = success
                
        # Fill textareas
        for field, config in self.FIELD_MAPPINGS.items():
            if config['type'] == 'textarea' and field in user_data:
                success = self._fill_textarea(
                    config['field_name'],
                    user_data[field]
                )
                results[field] = success
                
        # Special handling for product name (without memory)
        if 'brand' in user_data and 'model' in user_data:
            product_name = f"{user_data['brand']} {user_data['model']}"
            success = self._fill_input('txtBrandModel', product_name)
            results['product_name'] = success
            
        # Enhanced remarks with memory info
        if 'memory' in user_data:
            remarks = user_data.get('remarks', '')
            if remarks:
                remarks = f"Memory: {user_data['memory']} | {remarks}"
            else:
                remarks = f"Memory: {user_data['memory']}"
            success = self._fill_textarea('areaRemarks', remarks)
            results['remarks_with_memory'] = success
            
        return results
    
    def _fill_dropdown(self, field_name: str, value: str, mapping: Dict) -> bool:
        """Fill a dropdown field"""
        try:
            # Map user value to form value
            form_value = mapping.get(value, value)
            
            # Use JavaScript to set value
            self.driver.execute_script(f"""
                var select = document.querySelector('select[name="{field_name}"]');
                if (select) {{
                    // Try to find option by mapped value
                    var found = false;
                    for (var i = 0; i < select.options.length; i++) {{
                        var option = select.options[i];
                        if (option.value.toLowerCase().includes('{form_value.lower()}') ||
                            option.text.toLowerCase().includes('{value.lower()}')) {{
                            select.value = option.value;
                            select.dispatchEvent(new Event('change'));
                            found = true;
                            console.log('Selected {value} in {field_name}');
                            break;
                        }}
                    }}
                    if (!found && select.options.length > 1) {{
                        // Select first non-empty option
                        select.selectedIndex = 1;
                        select.dispatchEvent(new Event('change'));
                    }}
                    return true;
                }}
                return false;
            """)
            print(f"✅ Dropdown {field_name}: {value}")
            return True
        except Exception as e:
            print(f"❌ Failed to fill dropdown {field_name}: {e}")
            return False
    
    def _fill_input(self, field_name: str, value: any) -> bool:
        """Fill an input field"""
        try:
            self.driver.execute_script(f"""
                var input = document.querySelector('input[name="{field_name}"]');
                if (input) {{
                    input.value = '{value}';
                    input.dispatchEvent(new Event('change'));
                    input.dispatchEvent(new Event('input'));
                    console.log('Filled {field_name} with {value}');
                    return true;
                }}
                return false;
            """)
            print(f"✅ Input {field_name}: {value}")
            return True
        except Exception as e:
            print(f"❌ Failed to fill input {field_name}: {e}")
            return False
    
    def _fill_textarea(self, field_name: str, value: str) -> bool:
        """Fill a textarea field"""
        try:
            # Escape quotes in the value
            escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
            
            self.driver.execute_script(f"""
                var textarea = document.querySelector('textarea[name="{field_name}"]');
                if (textarea) {{
                    textarea.value = "{escaped_value}";
                    textarea.dispatchEvent(new Event('change'));
                    console.log('Filled textarea {field_name}');
                    return true;
                }}
                return false;
            """)
            print(f"✅ Textarea {field_name}: {value[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Failed to fill textarea {field_name}: {e}")
            return False
    
    def analyze_form_errors(self) -> List[str]:
        """Analyze form for validation errors"""
        errors = self.driver.execute_script("""
            var errors = [];
            
            // Look for error messages
            var errorElements = document.querySelectorAll(
                '.error, .alert-danger, .invalid-feedback, ' +
                '[class*="error"], [class*="alert"], .text-danger'
            );
            
            errorElements.forEach(function(el) {
                var text = el.textContent.trim();
                if (text && !errors.includes(text)) {
                    errors.push(text);
                }
            });
            
            // Check for required fields
            var requiredFields = document.querySelectorAll('[required]');
            requiredFields.forEach(function(field) {
                if (!field.value && field.offsetParent !== null) {
                    var label = field.labels ? field.labels[0]?.textContent : field.name;
                    errors.push('Required field empty: ' + (label || field.name));
                }
            });
            
            return errors;
        """)
        
        return errors
    
    def get_missing_fields(self) -> List[str]:
        """Get list of empty required fields"""
        return self.driver.execute_script("""
            var missing = [];
            var form = document.querySelector('form');
            if (form) {
                var fields = form.querySelectorAll('[required]');
                fields.forEach(function(field) {
                    if (!field.value && field.offsetParent !== null) {
                        missing.push(field.name || field.id);
                    }
                });
            }
            return missing;
        """)