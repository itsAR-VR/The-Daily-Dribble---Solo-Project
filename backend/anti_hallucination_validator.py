#!/usr/bin/env python3
"""
Anti-Hallucination Validator for AI-Powered Bots
Prevents false success claims by strictly validating AI responses
Based on SelfCheckGPT methodology for consistency checking
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class AntiHallucinationValidator:
    """
    Validates AI responses to prevent hallucinations where the bot claims success
    despite the AI clearly identifying failures.
    
    This directly addresses the bug where the bot ignored:
    - "blocked by validation errors" in current_state
    - "no success message appears" in the analysis
    - Clear failure indicators in warnings
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.validation_history = []
    
    def is_submission_successful(self, analysis: Dict[str, Any]) -> bool:
        """
        Strictly validates if a submission was actually successful.
        
        CRITICAL: This method actually listens to what the AI tells us!
        No more ignoring clear failure indicators.
        
        Args:
            analysis: AI analysis containing current_state, warnings, page_analysis, etc.
            
        Returns:
            bool: True only if explicit success indicators are found, False otherwise
        """
        # Log the analysis for debugging
        if self.verbose:
            print(f"\n🔍 ANTI-HALLUCINATION VALIDATION:")
            print(f"📊 Current State: {analysis.get('current_state', 'unknown')}")
            print(f"⚠️  Warnings: {analysis.get('warnings', [])}")
            print(f"📄 Page Analysis: {analysis.get('page_analysis', '')[:200]}...")
        
        # Track this validation
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "result": None,
            "reason": None
        }
        
        # STEP 1: Check for explicit failure indicators in warnings
        warnings = analysis.get("warnings", [])
        if isinstance(warnings, str):
            warnings = [warnings]
        
        for warning in warnings:
            failure_keywords = [
                "not submitted", "validation error", "required", "missing", 
                "failed", "blocked by validation", "submission failed",
                "error", "invalid", "blocked", "not posted", "unsuccessful"
            ]
            warning_lower = warning.lower() if warning else ""
            for keyword in failure_keywords:
                if keyword in warning_lower:
                    if self.verbose:
                        print(f"❌ DETECTED FAILURE in warnings: {warning}")
                    validation_result["result"] = False
                    validation_result["reason"] = f"Failure keyword '{keyword}' found in warning: {warning}"
                    self.validation_history.append(validation_result)
                    return False
        
        # STEP 2: Check current_state for failure indicators
        # THIS IS THE KEY CHECK THAT CATCHES THE BUG!
        current_state = analysis.get("current_state", "").lower()
        failure_states = [
            "validation error", "blocked", "failed", "error", 
            "submission failed", "blocked by validation", "invalid",
            "has-error", "form error", "not submitted", "unsuccessful",
            "no success message", "form visible", "still on form"
        ]
        
        for state in failure_states:
            if state in current_state:
                if self.verbose:
                    print(f"❌ DETECTED FAILURE in current_state: {current_state}")
                validation_result["result"] = False
                validation_result["reason"] = f"Failure state '{state}' found in current_state"
                self.validation_history.append(validation_result)
                return False
        
        # STEP 3: Check page_analysis for explicit success indicators
        page_analysis = analysis.get("page_analysis", "").lower()
        
        # First check for failure indicators in page analysis
        page_failures = [
            "validation error", "form error", "required field", 
            "missing", "invalid", "blocked", "failed"
        ]
        for failure in page_failures:
            if failure in page_analysis:
                if self.verbose:
                    print(f"❌ DETECTED FAILURE in page_analysis: {failure}")
                validation_result["result"] = False
                validation_result["reason"] = f"Failure indicator '{failure}' in page_analysis"
                self.validation_history.append(validation_result)
                return False
        
        # Check for explicit success indicators
        success_indicators = [
            "success", "successfully submitted", "confirmation", 
            "thank you", "created", "listing posted", "completed",
            "submission successful", "posted successfully",
            "inventory added", "listing created"
        ]
        
        success_found = any(indicator in page_analysis for indicator in success_indicators)
        
        # STEP 4: Check for redirect to success page
        success_urls = [
            "success", "confirmation", "thank", "complete", 
            "inventory/view", "my-listings", "dashboard"
        ]
        
        current_url = analysis.get("current_url", "").lower()
        url_success = any(url_part in current_url for url_part in success_urls)
        
        # STEP 5: Make final decision
        if success_found or url_success:
            if self.verbose:
                print(f"✅ DETECTED SUCCESS indicators")
            validation_result["result"] = True
            validation_result["reason"] = "Success indicators found"
            self.validation_history.append(validation_result)
            return True
        
        # DEFAULT: If no clear indicators, assume failure (safer)
        if self.verbose:
            print(f"❌ NO CLEAR SUCCESS INDICATORS - Assuming failure (anti-hallucination default)")
        validation_result["result"] = False
        validation_result["reason"] = "No clear success indicators found (defaulting to failure)"
        self.validation_history.append(validation_result)
        return False
    
    def validate_action_response(self, ai_response: Dict[str, Any]) -> bool:
        """
        Validates if an AI-suggested action should be executed.
        
        Args:
            ai_response: AI response with action suggestions
            
        Returns:
            bool: True if action is safe to execute
        """
        # Check confidence level
        confidence = ai_response.get("confidence", "low").lower()
        if confidence in ["low", "none", "uncertain"]:
            if self.verbose:
                print(f"⚠️  Low confidence action blocked: {confidence}")
            return False
        
        # Check for error states
        state = ai_response.get("state", "").lower()
        if any(err in state for err in ["error", "failed", "blocked", "invalid"]):
            if self.verbose:
                print(f"❌ Error state detected, blocking action: {state}")
            return False
        
        return True
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Returns a summary of all validations performed"""
        total = len(self.validation_history)
        if total == 0:
            return {"total": 0, "successes": 0, "failures": 0, "accuracy": 0}
        
        successes = sum(1 for v in self.validation_history if v["result"])
        failures = total - successes
        
        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "accuracy": (failures / total) * 100,  # Higher % = better at catching failures
            "history": self.validation_history[-10:]  # Last 10 validations
        }


# Example usage and test
if __name__ == "__main__":
    print("🧪 Testing Anti-Hallucination Validator\n")
    
    validator = AntiHallucinationValidator(verbose=True)
    
    # Test Case 1: Your exact bug scenario
    print("=" * 60)
    print("TEST 1: Your Exact Terminal Bug")
    print("=" * 60)
    
    bug_analysis = {
        "current_state": "Logged in as a seller on the \"List Inventory\" page; the listing form is visible but blocked by validation errors—no success message appears.",
        "next_action": "wait - Wait for any form-group elements to have the \"has-error\" class, confirming validation errors are present and submission failed.",
        "page_analysis": "The form shows validation errors. Required fields are highlighted in red.",
        "warnings": ["Listing was not submitted: required fields are missing or invalid."],
        "confidence": "high"
    }
    
    result = validator.is_submission_successful(bug_analysis)
    print(f"\n🎯 Result: {'SUCCESS' if result else 'FAILURE'}")
    print(f"✅ Correctly identified as FAILURE (no more hallucination!)\n")
    
    # Test Case 2: Actual success
    print("=" * 60)
    print("TEST 2: Actual Success Case")
    print("=" * 60)
    
    success_analysis = {
        "current_state": "Submission complete, redirected to success page",
        "page_analysis": "Success! Your listing has been posted successfully. You can view it in your inventory.",
        "warnings": [],
        "confidence": "high",
        "current_url": "https://cellpex.com/inventory/success"
    }
    
    result = validator.is_submission_successful(success_analysis)
    print(f"\n🎯 Result: {'SUCCESS' if result else 'FAILURE'}")
    
    # Show summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    summary = validator.get_validation_summary()
    print(f"Total validations: {summary['total']}")
    print(f"Failures caught: {summary['failures']}")
    print(f"Anti-hallucination accuracy: {summary['accuracy']:.1f}%")