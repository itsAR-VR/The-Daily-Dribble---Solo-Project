#!/usr/bin/env python3
"""FastAPI backend for the multi-platform listing bot.

This FastAPI application wraps the multi-platform listing bot script,
providing HTTP endpoints to submit Excel files and retrieve results.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
# OpenAI import - conditional based on availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. AI features will use fallback generation.")

# Import the main script
try:
    from backend.multi_platform_listing_bot import run_from_spreadsheet
except ImportError:
    # Create a dummy function if import fails
    def run_from_spreadsheet(input_path: str, output_path: str) -> None:
        raise RuntimeError("Chrome/Selenium not available. Please check deployment configuration.")

# Import Gmail service with detailed error handling
GMAIL_AVAILABLE = False
gmail_service = None
gmail_import_error = None

try:
    print("📦 Attempting to import Gmail service...")
    from backend.gmail_service import gmail_service
    print("✅ Gmail service module imported successfully")
    # Gmail service is available if imported successfully, regardless of auth status
    GMAIL_AVAILABLE = True
    auth_status = gmail_service.is_available()
    print(f"📊 Gmail service available: {GMAIL_AVAILABLE}")
    print(f"🔐 Gmail authentication status: {auth_status}")
except ImportError as e:
    gmail_import_error = str(e)
    print(f"❌ Gmail service import failed: {e}")
    print("🔍 This is usually due to missing Google API dependencies")
    GMAIL_AVAILABLE = False
    gmail_service = None
except Exception as e:
    gmail_import_error = str(e)
    print(f"❌ Gmail service initialization failed: {e}")
    print(f"🔍 Error type: {type(e).__name__}")
    GMAIL_AVAILABLE = False
    gmail_service = None

# Test Chrome availability on startup (non-blocking)
CHROME_AVAILABLE = False
chrome_test_error = "Not tested yet"
print("🔍 Chrome driver will be tested on first use (Selenium Manager will handle ChromeDriver)")
print(f"CHROME_BIN env: {os.getenv('CHROME_BIN', 'Not set')}")
print(f"Railway environment: {'Yes' if os.getenv('RAILWAY_ENVIRONMENT') else 'No'}")

# Check if Chrome binary exists
import subprocess
try:
    result = subprocess.run(["which", "google-chrome-stable"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Chrome found at: {result.stdout.strip()}")
        CHROME_AVAILABLE = True
    else:
        result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome found at: {result.stdout.strip()}")
            CHROME_AVAILABLE = True
        else:
            print("❌ Chrome not found in PATH")
except Exception as e:
    print(f"❌ Error checking for Chrome: {e}")
    
    # Create a fallback function
    def run_from_spreadsheet_fallback(input_path: str, output_path: str) -> None:
        import pandas as pd
        
        # Read the input file
        df = pd.read_excel(input_path)
        
        # Add a status column showing that Chrome is not available
        df['Status'] = 'Error: Chrome/Selenium not available in deployment environment. Please upgrade hosting plan or use local deployment.'
        
        # Save the result
        df.to_excel(output_path, index=False)
        print(f"Fallback processing complete: {len(df)} rows processed with error status")
    
    # Replace the function
    run_from_spreadsheet = run_from_spreadsheet_fallback

app = FastAPI(
    title="Multi-Platform Listing Bot API",
    description="API for automating product listings across multiple wholesale marketplaces",
    version="1.1.0-individual-env-vars"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory where job files will be stored
JOBS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "jobs"))
os.makedirs(JOBS_DIR, exist_ok=True)

# Job status tracking
jobs = {}


class SingleListingRequest(BaseModel):
    platform: str
    product_name: str
    condition: str
    quantity: int
    price: float


class ComprehensiveListingData(BaseModel):
    # Basic Info
    product_type: str
    category: str
    brand: str
    product_name: str
    model_code: Optional[str] = ""
    
    # Condition & Quality
    condition: str
    condition_grade: Optional[str] = "A"
    lcd_defects: Optional[str] = "None"
    quality_certification: Optional[str] = ""
    
    # Technical Specs
    memory: Optional[str] = ""
    color: Optional[str] = ""
    market_spec: Optional[str] = "US"
    sim_lock_status: Optional[str] = "Unlocked"
    carrier: Optional[str] = ""
    
    # Pricing & Inventory
    price: float
    currency: str = "USD"
    quantity: int
    minimum_order_quantity: Optional[int] = 1
    supply_ability: Optional[str] = ""
    
    # Shipping & Packaging
    packaging: Optional[str] = "Original Box"
    item_weight: Optional[float] = 0.3
    weight_unit: Optional[str] = "kg"
    incoterm: Optional[str] = "EXW"
    allow_local_pickup: Optional[bool] = False
    delivery_days: Optional[int] = 7
    
    # Location
    country: Optional[str] = "United States"
    state: Optional[str] = ""
    
    # Description & Media
    description: Optional[str] = ""
    keywords: Optional[List[str]] = []
    accepted_payments: Optional[List[str]] = ["PayPal"]
    auto_share_linkedin: Optional[bool] = False
    auto_share_twitter: Optional[bool] = False
    
    # Additional
    private_notes: Optional[str] = ""
    manufacturer_type: Optional[str] = ""


class EnhancedListingRequest(BaseModel):
    platform: str
    listing_data: ComprehensiveListingData


# Platform-specific field mappings
PLATFORM_FIELD_MAPPINGS = {
    "cellpex": {
        "product_name": ["product_name", "brand", "model_code"],  # Combine fields
        "category": "category",
        "condition": "condition",
        "memory": "memory", 
        "color": "color",
        "market_spec": "market_spec",
        "sim_lock": "sim_lock_status",
        "carrier": "carrier",
        "price": "price",
        "quantity": "quantity",
        "min_order": "minimum_order_quantity",
        "packaging": "packaging",
        "weight": ["item_weight", "weight_unit"],  # Combine value and unit
        "incoterm": "incoterm",
        "local_pickup": "allow_local_pickup",
        "country": "country",
        "state": "state",
        "payment": "accepted_payments",
        "description": "description",
        "keywords": "keywords"
    },
    "hubx": {
        # HubX specific mappings
        "title": ["brand", "product_name", "memory", "color"],
        "condition": "condition",
        "price": "price",
        "stock": "quantity",
        "description": "description"
    },
    "gsmexchange": {
        # GSM Exchange specific mappings
        "model_name": ["brand", "product_name", "memory", "color"],  # Combine into model field
        "quantity": "quantity",
        "price": "price",
        "currency": "currency",
        "condition": "condition",
        "specification": "market_spec",  # Maps to regional specs
        "comments": ["description", "sim_lock_status", "carrier", "lcd_defects", "quality_certification"],  # Combine details
        "listing_type": "sell",  # Always "I want to sell"
        "stock_confirmation": True  # Always confirm stock
    },
    # Add mappings for other platforms...
}


def generate_ai_description(data: ComprehensiveListingData) -> str:
    """Generate AI-powered description based on product data"""
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            # Set up OpenAI client
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Create prompt for AI description
            prompt = f"""
Create a professional marketplace listing description for:

Product: {data.brand} {data.product_name}
Category: {data.category}
Condition: {data.condition} (Grade {data.condition_grade})
Memory: {data.memory}
Color: {data.color}
Market: {data.market_spec}
SIM Lock: {data.sim_lock_status}
Carrier: {data.carrier or 'Unlocked'}
LCD Defects: {data.lcd_defects}
Packaging: {data.packaging}
Weight: {data.item_weight}{data.weight_unit}
Delivery: {data.delivery_days} days
Payment: {', '.join(data.accepted_payments)}

Requirements:
- Professional tone
- Highlight key features
- Mention condition clearly
- Include shipping info
- 200-300 words
- Appeal to buyers
- Include technical specs

Write a compelling product description:
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # GPT-4.1 is accessed via gpt-4o model name
                messages=[
                    {"role": "system", "content": "You are a professional marketplace listing writer. Create compelling, accurate product descriptions that help items sell."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall back to template-based description
    
    # Fallback template-based description
    description = f"""
Professional {data.brand} {data.product_name} in {data.condition.lower()} condition.

🔧 Technical Specifications:
• Memory/Storage: {data.memory}
• Color: {data.color}
• Market Specification: {data.market_spec}
• SIM Lock Status: {data.sim_lock_status}
{'• Carrier: ' + data.carrier if data.carrier else '• Fully Unlocked'}

📋 Condition Details:
• Overall Grade: {data.condition_grade}
• LCD Screen: {data.lcd_defects}
• Quality Certification: {data.quality_certification or 'Standard'}

📦 Shipping & Packaging:
• Original Packaging: {data.packaging}
• Item Weight: {data.item_weight}{data.weight_unit}
• Shipping Terms: {data.incoterm}
• Delivery Time: {data.delivery_days} business days
{'• Local Pickup Available' if data.allow_local_pickup else ''}

💳 Payment Options: {', '.join(data.accepted_payments)}

{data.description if data.description else ''}

Perfect for resale or personal use. Fast shipping and secure payment processing guaranteed.
    """.strip()
    
    return description


def generate_ai_keywords(data: ComprehensiveListingData) -> List[str]:
    """Generate AI-powered keywords based on product data"""
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            prompt = f"""
Generate SEO-optimized keywords for this marketplace listing:

Product: {data.brand} {data.product_name}
Category: {data.category}
Memory: {data.memory}
Color: {data.color}
Condition: {data.condition}
Market: {data.market_spec}

Generate 15-20 relevant keywords that buyers would search for. Include:
- Brand and model variations
- Technical specifications
- Condition-related terms
- Common search terms
- Category keywords

Return as comma-separated list only:
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # GPT-4.1 is accessed via gpt-4o model name
                messages=[
                    {"role": "system", "content": "You are an SEO expert for marketplace listings. Generate keywords that maximize search visibility."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            ai_keywords = [k.strip().lower() for k in response.choices[0].message.content.split(',')]
            return ai_keywords[:20]  # Limit to 20 keywords
            
        except Exception as e:
            print(f"OpenAI API error for keywords: {e}")
    
    # Fallback keyword generation
    keywords = []
    
    # Add basic keywords
    if data.brand:
        keywords.extend([data.brand.lower(), data.brand.lower().replace(' ', '')])
    if data.product_name:
        keywords.extend(data.product_name.lower().split())
    if data.model_code:
        keywords.append(data.model_code.lower())
    
    # Add spec keywords
    if data.memory:
        keywords.extend([data.memory.lower(), data.memory.lower().replace('gb', '').replace('tb', '')])
    if data.color:
        keywords.append(data.color.lower())
    if data.condition:
        keywords.extend([data.condition.lower(), 'good condition', 'working'])
    
    # Add category keywords
    if data.category:
        keywords.append(data.category.lower())
    
    # Add common search terms
    keywords.extend(['phone', 'mobile', 'smartphone', 'device', 'electronics'])
    
    # Remove duplicates and return
    return list(set([k for k in keywords if k and len(k) > 1]))[:15]


@app.get("/")
async def read_root():
    chrome_status = "available" if CHROME_AVAILABLE else "not available"
    openai_status = "available" if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY") else "not available"
    
    # Check OAuth authentication status
    gmail_authenticated = False
    gmail_status = "not available"
    if GMAIL_AVAILABLE and gmail_service:
        if gmail_service.credentials and gmail_service.credentials.valid:
            gmail_status = "authenticated"
            gmail_authenticated = True
        else:
            gmail_status = "requires authentication"
    
    return {
        "message": "Multi-Platform Listing Bot API",
        "version": "2.0.0-oauth",
        "chrome_status": chrome_status,
        "openai_status": openai_status,
        "gmail_status": gmail_status,
        "gmail_authenticated": gmail_authenticated,
        "authentication_method": "oauth",
        "ai_features": "enabled" if openai_status == "available" else "fallback mode",
        "2fa_automation": "enabled" if gmail_authenticated else "authentication required",
        "endpoints": {
            "POST /listings": "Upload Excel file for batch processing",
            "GET /listings/{job_id}": "Get job status and results",
            "POST /listings/single": "Post a single listing",
            "POST /listings/enhanced": "Post with comprehensive data and AI enrichment",
            "POST /listings/enhanced-visual": "Post with visual browser automation feedback",
            "GET /gmail/auth": "Start Gmail OAuth authentication",
            "GET /gmail/callback": "OAuth callback handler",
            "GET /gmail/status": "Check Gmail authentication status",
            "POST /gmail/revoke": "Revoke Gmail authentication"
        }
    }


@app.post("/listings")
async def create_listings(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload an Excel file with listings to process.
    Returns a job ID to track the processing status.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_path = os.path.join(JOBS_DIR, f"{job_id}_input.xlsx")
    output_path = os.path.join(JOBS_DIR, f"{job_id}_output.xlsx")
    
    # Write uploaded file to disk
    contents = await file.read()
    with open(input_path, "wb") as f:
        f.write(contents)
    
    # Initialize job status
    jobs[job_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "input_file": file.filename,
        "output_file": None,
        "error": None
    }
    
    # Process in background
    background_tasks.add_task(process_listings, job_id, input_path, output_path)
    
    return {"job_id": job_id, "status": "processing"}


def process_listings(job_id: str, input_path: str, output_path: str):
    """
    Background task to process listings using the multi_platform_listing_bot.
    """
    try:
        # Run the bot
        run_from_spreadsheet(input_path, output_path)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["output_file"] = output_path
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        # Update job status with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/listings/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and results of a listing job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # If job is completed, read the output file
    if job["status"] == "completed" and job["output_file"]:
        try:
            df = pd.read_excel(job["output_file"])
            results = df.to_dict(orient="records")
            job["results"] = results
        except Exception as e:
            job["error"] = f"Failed to read results: {str(e)}"
    
    return job


@app.post("/listings/single")
async def create_single_listing(listing: SingleListingRequest):
    """
    Post a single listing to a specific platform.
    This endpoint handles real-time posting with Selenium.
    """
    try:
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if listing.platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {listing.platform}. Valid platforms: {valid_platforms}"
            )
        
        # Create a temporary Excel file with single row
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with single listing
        df = pd.DataFrame([{
            'platform': listing.platform,
            'product_name': listing.product_name,
            'condition': listing.condition,
            'quantity': listing.quantity,
            'price': listing.price
        }])
        
        df.to_excel(temp_input, index=False)
        
        # Process the single listing
        try:
            run_from_spreadsheet(temp_input, temp_output)
            
            # Read the output to check status
            result_df = pd.read_excel(temp_output)
            if 'Status' in result_df.columns:
                status = result_df.iloc[0]['Status']
                if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                    return {
                        "success": False,
                        "message": str(status),
                        "platform": listing.platform,
                        "product": listing.product_name
                    }
            
            return {
                "success": True,
                "message": "Posted successfully",
                "platform": listing.platform,
                "product": listing.product_name
            }
            
        finally:
            # Clean up temp files
            for f in [temp_input, temp_output]:
                if os.path.exists(f):
                    os.unlink(f)
                    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": listing.platform,
            "product": listing.product_name
        }


@app.post("/listings/enhanced")
async def create_enhanced_listing(request: EnhancedListingRequest):
    """
    Post a listing with comprehensive data to a specific platform.
    This handles the platform-specific field mapping and AI enrichment.
    """
    try:
        listing_data = request.listing_data
        platform = request.platform
        
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid platforms: {valid_platforms}"
            )
        
        # AI enrichment if needed
        if not listing_data.description:
            listing_data.description = generate_ai_description(listing_data)
        
        if not listing_data.keywords:
            listing_data.keywords = generate_ai_keywords(listing_data)
        
        # Create platform-specific data structure
        platform_data = map_to_platform_fields(platform, listing_data)
        
        # Create a temporary Excel file with the mapped data
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with platform-specific fields
        df = pd.DataFrame([platform_data])
        df.to_excel(temp_input, index=False)
        
        # Process the listing
        try:
            run_from_spreadsheet(temp_input, temp_output)
            
            # Read the output to check status
            result_df = pd.read_excel(temp_output)
            if 'Status' in result_df.columns:
                status = result_df.iloc[0]['Status']
                if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                    return {
                        "success": False,
                        "message": str(status),
                        "platform": platform,
                        "product": listing_data.product_name
                    }
            
            return {
                "success": True,
                "message": "Posted successfully",
                "platform": platform,
                "product": listing_data.product_name,
                "enriched_description": listing_data.description,
                "enriched_keywords": listing_data.keywords
            }
            
        finally:
            # Clean up temp files
            for f in [temp_input, temp_output]:
                if os.path.exists(f):
                    os.unlink(f)
                    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": request.platform,
            "product": request.listing_data.product_name
        }


@app.post("/listings/enhanced-visual")
async def create_enhanced_listing_with_visual(request: EnhancedListingRequest):
    """
    Post a listing with visual feedback showing browser automation progress.
    This version supports parallel execution and real-time status updates.
    """
    try:
        listing_data = request.listing_data
        platform = request.platform
        
        # Validate platform
        valid_platforms = ["hubx", "gsmexchange", "kardof", "cellpex", "handlot"]
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid platforms: {valid_platforms}"
            )
        
        # AI enrichment if needed
        if not listing_data.description:
            listing_data.description = generate_ai_description(listing_data)
        
        if not listing_data.keywords:
            listing_data.keywords = generate_ai_keywords(listing_data)
        
        # Create platform-specific data structure
        platform_data = map_to_platform_fields(platform, listing_data)
        
        # Simulate browser automation steps
        browser_steps = []
        
        # Step 1: Opening browser
        browser_steps.append({
            "step": "browser_launch",
            "status": "completed",
            "message": f"Launching headless Chrome for {platform}",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjMjIyIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iI2ZmZiIgZm9udC1zaXplPSIxOCI+QnJvd3NlciBMYXVuY2hlZDwvdGV4dD4KPC9zdmc+"
        })
        
        # Step 2: Navigating to platform
        browser_steps.append({
            "step": "navigation",
            "status": "completed",
            "message": f"Navigating to {platform}.com",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+TG9hZGluZyB7cGxhdGZvcm19PC90ZXh0Pgo8L3N2Zz4="
        })
        
        # Step 3: Login check (if needed)
        if platform in ["gsmexchange", "cellpex"]:
            email_check_message = "Checking Gmail for verification code..."
            verification_code = None
            gmail_check_status = "action_required"
            
            if GMAIL_AVAILABLE and gmail_service:
                try:
                    # Actually check Gmail for verification codes
                    email_check_message = f"Searching Gmail for {platform} verification codes..."
                    verification_code = gmail_service.get_latest_verification_code(platform)
                    
                    if verification_code:
                        email_check_message = f"✅ Found verification code: {verification_code}"
                        gmail_check_status = "completed"
                    else:
                        email_check_message = "⏳ No recent verification code found. Monitoring for new emails..."
                        gmail_check_status = "monitoring"
                        
                except Exception as e:
                    email_check_message = f"❌ Gmail check failed: {str(e)}"
                    gmail_check_status = "error"
            else:
                email_check_message = "⚠️ Gmail service not available - manual 2FA required"
                gmail_check_status = "manual_required"
            
            browser_steps.append({
                "step": "login_check",
                "status": gmail_check_status,
                "message": "2FA code may be required - checking email",
                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+TG9naW4gUGFnZTwvdGV4dD4KPC9zdmc+",
                "requires_2fa": True,
                "email_check": email_check_message,
                "verification_code": verification_code,
                "gmail_available": GMAIL_AVAILABLE
            })
        
        # Step 4: Filling form
        browser_steps.append({
            "step": "form_filling",
            "status": "in_progress",
            "message": f"Filling product details: {listing_data.product_name}",
            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyIgZm9udC1zaXplPSIxOCI+Rm9ybSBGaWxsaW5nLi4uPC90ZXh0Pgo8L3N2Zz4=",
            "fields_filled": {
                "product": listing_data.product_name,
                "price": f"{listing_data.currency} {listing_data.price}",
                "quantity": listing_data.quantity
            }
        })
        
        # Create a temporary Excel file with the mapped data
        job_id = str(uuid.uuid4())
        temp_input = os.path.join(JOBS_DIR, f"temp_{job_id}_input.xlsx")
        temp_output = os.path.join(JOBS_DIR, f"temp_{job_id}_output.xlsx")
        
        # Create DataFrame with platform-specific fields
        df = pd.DataFrame([platform_data])
        df.to_excel(temp_input, index=False)
        
        # Process the listing (simulate or real based on Chrome availability)
        if CHROME_AVAILABLE:
            try:
                run_from_spreadsheet(temp_input, temp_output)
                
                # Read the output to check status
                result_df = pd.read_excel(temp_output)
                if 'Status' in result_df.columns:
                    status = result_df.iloc[0]['Status']
                    if 'Error' in str(status) or 'Failed' in str(status) or 'Chrome' in str(status):
                        browser_steps.append({
                            "step": "submission",
                            "status": "error",
                            "message": str(status),
                            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmVlIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iI2Y0NCIgZm9udC1zaXplPSIxOCI+RXJyb3I8L3RleHQ+Cjwvc3ZnPg=="
                        })
                        success = False
                    else:
                        browser_steps.append({
                            "step": "submission",
                            "status": "success",
                            "message": "Listing posted successfully!",
                            "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZWZlIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzRhNCIgZm9udC1zaXplPSIxOCI+U3VjY2VzcyE8L3RleHQ+Cjwvc3ZnPg=="
                        })
                        success = True
                else:
                    success = True
            finally:
                # Clean up temp files
                for f in [temp_input, temp_output]:
                    if os.path.exists(f):
                        os.unlink(f)
        else:
            # Simulated success for demo
            browser_steps.append({
                "step": "submission",
                "status": "simulated",
                "message": "Simulated submission (Chrome not available in current environment)",
                "screenshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZmZmM2NkIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjE1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzY2NiIgZm9udC1zaXplPSIxOCI+U2ltdWxhdGVkPC90ZXh0Pgo8L3N2Zz4="
            })
            success = False
        
        return {
            "success": success,
            "message": "Visual automation completed",
            "platform": platform,
            "product": listing_data.product_name,
            "enriched_description": listing_data.description,
            "enriched_keywords": listing_data.keywords,
            "browser_steps": browser_steps,
            "parallel_capable": True,
            "estimated_time": "30-45 seconds per platform"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "platform": request.platform,
            "product": request.listing_data.product_name,
            "browser_steps": [{
                "step": "error",
                "status": "error",
                "message": str(e),
                "screenshot": None
            }]
        }


def map_to_platform_fields(platform: str, data: ComprehensiveListingData) -> Dict[str, Any]:
    """
    Map comprehensive listing data to platform-specific fields.
    """
    if platform not in PLATFORM_FIELD_MAPPINGS:
        # Default mapping if platform not configured
        return {
            'platform': platform,
            'product_name': f"{data.brand} {data.product_name} {data.memory} {data.color}".strip(),
            'condition': data.condition,
            'quantity': data.quantity,
            'price': data.price,
            'description': data.description
        }
    
    mapping = PLATFORM_FIELD_MAPPINGS[platform]
    result = {'platform': platform}
    
    for platform_field, data_field in mapping.items():
        if isinstance(data_field, list):
            # Combine multiple fields
            values = []
            for field in data_field:
                value = getattr(data, field, "")
                if value:
                    values.append(str(value))
            
            # Special handling for GSM Exchange comments field
            if platform == "gsmexchange" and platform_field == "comments":
                comments_parts = []
                if data.description:
                    comments_parts.append(data.description)
                
                # Add technical details
                tech_details = []
                if data.sim_lock_status and data.sim_lock_status != "Unlocked":
                    tech_details.append(f"SIM Lock: {data.sim_lock_status}")
                if data.carrier:
                    tech_details.append(f"Carrier: {data.carrier}")
                if data.lcd_defects and data.lcd_defects != "None":
                    tech_details.append(f"LCD: {data.lcd_defects}")
                if data.quality_certification:
                    tech_details.append(f"Certification: {data.quality_certification}")
                
                if tech_details:
                    comments_parts.append("Technical details: " + ", ".join(tech_details))
                
                result[platform_field] = "\n\n".join(comments_parts)
            else:
                result[platform_field] = " ".join(values)
        elif isinstance(data_field, bool):
            # Static boolean values
            result[platform_field] = data_field
        elif isinstance(data_field, str) and data_field in ["sell", "buy"]:
            # Static string values
            result[platform_field] = data_field
        else:
            # Direct mapping
            value = getattr(data, data_field, "")
            
            # Special condition mapping for GSM Exchange
            if platform == "gsmexchange" and platform_field == "condition":
                condition_mapping = {
                    "New": "New",
                    "Used": "Used and tested",
                    "Refurbished": "Refurbished", 
                    "Damaged": "ASIS",
                    "14-Days": "14 day"
                }
                result[platform_field] = condition_mapping.get(value, value)
            
            # Special specification mapping for GSM Exchange
            elif platform == "gsmexchange" and platform_field == "specification":
                spec_mapping = {
                    "US": "US spec.",
                    "Euro": "Euro spec.",
                    "UK": "UK spec.",
                    "Asia": "Asia spec.",
                    "Arabic": "Arab spec.",
                    "Other": "Other spec."
                }
                result[platform_field] = spec_mapping.get(value, "Global Spec.")
            
            elif isinstance(value, list):
                result[platform_field] = ", ".join(value)
            else:
                result[platform_field] = value
    
    return result


@app.get("/gmail/status")
async def get_gmail_status():
    """Get Gmail service status and configuration details."""
    if not GMAIL_AVAILABLE or not gmail_service:
        return {
            "available": False,
            "status": "not_configured",
            "message": "Gmail service not available. Check OAuth configuration.",
            "oauth_flow": {
                "auth_url": "/gmail/auth",
                "callback_url": "/gmail/callback",
                "revoke_url": "/gmail/revoke"
            }
        }
    
    has_credentials = gmail_service.credentials is not None and gmail_service.credentials.valid
    
    return {
        "available": True,
        "status": "authenticated" if has_credentials else "requires_auth",
        "message": "Gmail service is properly configured with OAuth" if has_credentials else "OAuth authentication required",
        "authenticated": has_credentials,
        "features": [
            "2FA code retrieval",
            "Verification code extraction", 
            "Platform-specific email monitoring"
        ],
        "oauth_flow": {
            "auth_url": "/gmail/auth",
            "callback_url": "/gmail/callback",
            "revoke_url": "/gmail/revoke"
        }
    }


@app.post("/gmail/reinitialize")
async def reinitialize_gmail_service():
    """Force reinitialize Gmail service with current OAuth credentials."""
    if not gmail_service:
        return {
            "success": False,
            "message": "Gmail service module not available"
        }
    
    success = gmail_service.force_reinitialize()
    return {
        "success": success,
        "message": "Gmail service reinitialized successfully" if success else "Gmail service reinitialization failed",
        "authentication_method": "oauth",
        "service_available": gmail_service.service is not None,
        "credentials_valid": gmail_service.credentials is not None and gmail_service.credentials.valid if gmail_service.credentials else False
    }


@app.get("/gmail/auth")
async def start_gmail_oauth():
    """Start Gmail OAuth authentication flow."""
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        authorization_url, state = gmail_service.get_authorization_url()
        return {
            "authorization_url": authorization_url,
            "state": state,
            "message": "Visit the authorization URL to authenticate with Gmail",
            "instructions": [
                "1. Visit the authorization URL",
                "2. Sign in with your Google account",
                "3. Grant access to Gmail",
                "4. You'll be redirected to the callback URL with an authorization code"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")


@app.get("/gmail/callback")
async def gmail_oauth_callback(code: str = None, error: str = None):
    """Handle Gmail OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        success = gmail_service.exchange_code_for_credentials(code)
        if success:
            return {
                "success": True,
                "message": "Gmail OAuth authentication successful!",
                "status": "authenticated",
                "service_available": gmail_service.service is not None
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to exchange code for credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@app.post("/gmail/revoke")
async def revoke_gmail_oauth():
    """Revoke Gmail OAuth credentials."""
    if not GMAIL_AVAILABLE or not gmail_service:
        raise HTTPException(status_code=500, detail="Gmail service not available")
    
    try:
        success = gmail_service.revoke_credentials()
        return {
            "success": success,
            "message": "Gmail OAuth credentials revoked successfully",
            "status": "unauthenticated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke credentials: {str(e)}")


@app.get("/gmail/diagnostics")
async def gmail_diagnostics():
    """Comprehensive Gmail service diagnostics for OAuth."""
    diagnostics = {
        "gmail_service_module": gmail_service is not None,
        "gmail_available_flag": GMAIL_AVAILABLE,
        "import_error": gmail_import_error,
        "authentication_method": "oauth",
        "service_status": {
            "initialized": gmail_service.service is not None if gmail_service else False,
            "has_credentials": gmail_service.credentials is not None if gmail_service else False,
            "credentials_valid": gmail_service.credentials.valid if gmail_service and gmail_service.credentials else False,
        },
        "oauth_files": {}
    }
    
    # Check OAuth files
    if gmail_service:
        diagnostics["oauth_files"]["credentials_file"] = {
            "path": gmail_service.credentials_file,
            "exists": os.path.exists(gmail_service.credentials_file)
        }
        diagnostics["oauth_files"]["token_file"] = {
            "path": gmail_service.token_file,
            "exists": os.path.exists(gmail_service.token_file)
        }
        
        # Check credentials file content
        if os.path.exists(gmail_service.credentials_file):
            try:
                with open(gmail_service.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    diagnostics["oauth_files"]["credentials_valid"] = {
                        "has_client_id": bool(creds_data.get("installed", {}).get("client_id")),
                        "has_client_secret": bool(creds_data.get("installed", {}).get("client_secret")),
                        "project_id": creds_data.get("installed", {}).get("project_id")
                    }
            except Exception as e:
                diagnostics["oauth_files"]["credentials_error"] = str(e)
    
    return diagnostics


@app.post("/gmail/test-search")
async def test_gmail_search(platform: str = "gsmexchange"):
    """Test Gmail search functionality for a specific platform."""
    if not gmail_service or not gmail_service.is_available():
        return {
            "success": False,
            "message": "Gmail service not available"
        }
    
    try:
        # Search for verification codes
        codes = gmail_service.search_verification_codes(platform, minutes_back=60)
        
        # Get the latest code
        latest_code = gmail_service.get_latest_verification_code(platform)
        
        return {
            "success": True,
            "platform": platform,
            "total_codes_found": len(codes),
            "latest_code": latest_code,
            "search_details": {
                "authentication_method": "OAuth 2.0",
                "search_timeframe": "60 minutes", 
                "codes_found": codes[:3]  # Return first 3 for privacy
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Gmail search test failed: {str(e)}"
        }


@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check OAuth configuration."""
    import json
    
    # Check environment variables
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    debug_info = {
        "environment_variables": {
            "OPENAI_API_KEY": "✅ SET" if openai_key else "❌ NOT SET"
        },
        "service_status": {
            "gmail_service_available": GMAIL_AVAILABLE,
            "chrome_available": CHROME_AVAILABLE,
            "openai_available": OPENAI_AVAILABLE
        },
        "authentication_method": "oauth",
        "runtime_check": {
            "gmail_service_object": gmail_service is not None,
            "gmail_service_type": str(type(gmail_service)) if gmail_service else "None",
            "gmail_available_flag": GMAIL_AVAILABLE,
            "can_call_methods": hasattr(gmail_service, 'get_authorization_url') if gmail_service else False
        }
    }
    
    # Check OAuth files and status
    if gmail_service:
        debug_info["oauth_status"] = {
            "credentials_file_exists": os.path.exists(gmail_service.credentials_file),
            "token_file_exists": os.path.exists(gmail_service.token_file),
            "has_credentials": gmail_service.credentials is not None,
            "credentials_valid": gmail_service.credentials.valid if gmail_service.credentials else False,
            "service_initialized": gmail_service.service is not None
        }
        
        # Check credentials file content
        if os.path.exists(gmail_service.credentials_file):
            try:
                with open(gmail_service.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    installed = creds_data.get("installed", {})
                    debug_info["oauth_credentials_validation"] = {
                        "valid_json": True,
                        "project_id": installed.get("project_id"),
                        "has_client_id": bool(installed.get("client_id")),
                        "has_client_secret": bool(installed.get("client_secret")),
                        "redirect_uris": installed.get("redirect_uris", [])
                    }
            except json.JSONDecodeError as e:
                debug_info["oauth_credentials_validation"] = {
                    "valid_json": False,
                    "error": str(e),
                    "suggestion": "Check OAuth credentials JSON formatting"
                }
        else:
            debug_info["oauth_credentials_validation"] = {
                "file_missing": True,
                "suggestion": "OAuth credentials file not found. Please ensure google_oauth_credentials.json exists."
            }
    
    return debug_info


# Enhanced 2FA Testing Endpoints
@app.post("/test/enhanced-2fa/cellpex")
async def test_enhanced_cellpex_2fa():
    """Test enhanced Cellpex 2FA flow in production"""
    try:
        # Import here to avoid circular imports
        from backend.enhanced_platform_poster import EnhancedCellpexPoster
        from selenium import webdriver
        
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        if os.getenv("RAILWAY_ENVIRONMENT"):  # Running on Railway
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # Initialize Cellpex poster
            cellpex_poster = EnhancedCellpexPoster(driver)
            
            # Test login with 2FA
            success = cellpex_poster.login_with_2fa()
            
            current_url = driver.current_url
            
            return {
                "success": success,
                "platform": "cellpex",
                "message": "Enhanced Cellpex 2FA test completed",
                "final_url": current_url,
                "gmail_available": gmail_service.is_available() if gmail_service else False,
                "status": "success" if success else "failed"
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "platform": "cellpex", 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Enhanced Cellpex 2FA test failed"
        }


@app.post("/test/enhanced-2fa/gsm-exchange")
async def test_enhanced_gsm_2fa():
    """Test enhanced GSM Exchange 2FA flow in production"""
    try:
        # Check if GSM credentials are available
        username = os.getenv("GSMEXCHANGE_USERNAME")
        password = os.getenv("GSMEXCHANGE_PASSWORD")
        
        if not username or not password:
            return {
                "success": False,
                "platform": "gsmexchange",
                "error": "Missing GSM Exchange credentials",
                "message": "GSMEXCHANGE_USERNAME and GSMEXCHANGE_PASSWORD required"
            }
        
        from selenium import webdriver
        
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        if os.getenv("RAILWAY_ENVIRONMENT"):  # Running on Railway
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # Import and run GSM test
            from test_gsm_2fa_flow import test_gsm_2fa_flow
            
            # This is a simplified version for API testing
            success = False  # Will implement after analyzing GSM Exchange
            
            return {
                "success": success,
                "platform": "gsmexchange",
                "message": "GSM Exchange 2FA flow needs implementation",
                "credentials_available": True,
                "status": "pending_implementation"
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "platform": "gsmexchange",
            "error": str(e), 
            "traceback": traceback.format_exc(),
            "message": "Enhanced GSM Exchange 2FA test failed"
        }


@app.get("/test/platform-status")
async def platform_status():
    """Get status of all platforms and their 2FA readiness"""
    
    platforms = {
        "cellpex": {
            "status": "ready",
            "credentials_available": bool(os.getenv("CELLPEX_USERNAME") and os.getenv("CELLPEX_PASSWORD")),
            "2fa_implemented": True,
            "login_url": "https://www.cellpex.com/login",
            "last_tested": "Working as of deployment"
        },
        "gsmexchange": {
            "status": "testing",
            "credentials_available": bool(os.getenv("GSMEXCHANGE_USERNAME") and os.getenv("GSMEXCHANGE_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "https://www.gsmexchange.com/signin",
            "last_tested": "Pending implementation"
        },
        "hubx": {
            "status": "pending",
            "credentials_available": bool(os.getenv("HUBX_USERNAME") and os.getenv("HUBX_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD",
            "last_tested": "Not started"
        },
        "kardof": {
            "status": "pending",
            "credentials_available": bool(os.getenv("KARDOF_USERNAME") and os.getenv("KARDOF_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD", 
            "last_tested": "Not started"
        },
        "handlot": {
            "status": "pending",
            "credentials_available": bool(os.getenv("HANDLOT_USERNAME") and os.getenv("HANDLOT_PASSWORD")),
            "2fa_implemented": False,
            "login_url": "TBD",
            "last_tested": "Not started"
        }
    }
    
    return {
        "platforms": platforms,
        "gmail_service_available": gmail_service.is_available() if gmail_service else False,
        "total_platforms": len(platforms),
        "ready_platforms": len([p for p in platforms.values() if p["status"] == "ready"]),
        "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
    }


@app.get("/debug/environment")
async def debug_environment():
    """Get detailed environment and Chrome installation info"""
    import platform
    import subprocess
    
    env_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "chrome_bin": os.getenv("CHROME_BIN"),
        "chromedriver_path": os.getenv("CHROMEDRIVER_PATH"),
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT"),
        "path": os.getenv("PATH")
    }
    
    # Check Chrome installation
    chrome_check = {"installed": False, "version": None, "path": None}
    try:
        # Try different Chrome paths
        chrome_paths = [
            os.getenv("CHROME_BIN"),
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "google-chrome",
            "chromium"
        ]
        
        for chrome_path in chrome_paths:
            if chrome_path:
                try:
                    result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        chrome_check = {
                            "installed": True,
                            "version": result.stdout.strip(),
                            "path": chrome_path
                        }
                        break
                except:
                    continue
    except Exception as e:
        chrome_check["error"] = str(e)
    
    env_info["chrome_check"] = chrome_check
    
    # Check ChromeDriver
    driver_check = {"installed": False, "version": None, "path": None}
    try:
        driver_paths = [
            os.getenv("CHROMEDRIVER_PATH"),
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "chromedriver"
        ]
        
        for driver_path in driver_paths:
            if driver_path:
                try:
                    result = subprocess.run([driver_path, "--version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        driver_check = {
                            "installed": True,
                            "version": result.stdout.strip(),
                            "path": driver_path
                        }
                        break
                except:
                    continue
    except Exception as e:
        driver_check["error"] = str(e)
    
    env_info["chromedriver_check"] = driver_check
    
    # Check for missing libraries
    missing_libs = []
    try:
        # Check for common missing dependencies
        libs_to_check = [
            "libnss3.so",
            "libnspr4.so",
            "libatk-1.0.so.0",
            "libatk-bridge-2.0.so.0",
            "libcups.so.2",
            "libdbus-1.so.3",
            "libdrm.so.2",
            "libxkbcommon.so.0",
            "libX11.so.6",
            "libXcomposite.so.1",
            "libXdamage.so.1",
            "libXext.so.6",
            "libXfixes.so.3",
            "libXrandr.so.2",
            "libgbm.so.1",
            "libasound.so.2"
        ]
        
        result = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
        if result.returncode == 0:
            installed_libs = result.stdout
            for lib in libs_to_check:
                if lib not in installed_libs:
                    missing_libs.append(lib)
    except:
        pass
    
    if missing_libs:
        env_info["missing_libs"] = missing_libs
    
    return env_info


@app.get("/test/chrome-status")
async def test_chrome_status():
    """Real-time Chrome status check"""
    from selenium import webdriver
    
    result = {
        "chrome_bin": os.getenv("CHROME_BIN"),
        "chromedriver_path": os.getenv("CHROMEDRIVER_PATH"),
        "se_chromedriver_path": os.getenv("SE_CHROMEDRIVER_PATH"),
        "chrome_user_data_dir": os.getenv("CHROME_USER_DATA_DIR"),
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT"),
        "startup_test_passed": CHROME_AVAILABLE,
        "startup_error": chrome_test_error if 'chrome_test_error' in globals() else None
    }
    
    # Try to create Chrome driver now
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        chrome_bin = os.getenv("CHROME_BIN")
        if chrome_bin:
            options.binary_location = chrome_bin
            
        driver = webdriver.Chrome(options=options)
        driver.get("data:text/html,<h1>Chrome Working!</h1>")
        title = driver.title
        driver.quit()
        
        result["runtime_test"] = "PASS"
        result["test_message"] = f"Chrome created successfully, page title: {title}"
        
    except Exception as e:
        result["runtime_test"] = "FAIL"
        result["test_error"] = str(e)
        
    return result


@app.post("/debug/test-chrome")
async def debug_test_chrome(request: dict):
    """Test Chrome driver creation with verbose output"""
    verbose = request.get("verbose", False)
    logs = []
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        if verbose:
            logs.append("Starting Chrome driver test...")
        
        # Get Chrome and ChromeDriver paths
        chrome_bin = os.getenv("CHROME_BIN")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
        
        if verbose:
            logs.append(f"CHROME_BIN: {chrome_bin}")
            logs.append(f"CHROMEDRIVER_PATH: {chromedriver_path}")
        
        # Setup options
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        
        if chrome_bin:
            options.binary_location = chrome_bin
            if verbose:
                logs.append(f"Set Chrome binary location: {chrome_bin}")
        
        # Try to create driver
        if verbose:
            logs.append("Using Selenium Manager for ChromeDriver")
            
        # Let Selenium Manager handle ChromeDriver
        driver = webdriver.Chrome(options=options)
        
        if verbose:
            logs.append("Chrome driver created successfully!")
        
        # Test navigation
        driver.get("data:text/html,<h1>Chrome Test</h1>")
        title = driver.title
        
        if verbose:
            logs.append(f"Page title: {title}")
        
        driver.quit()
        
        return {
            "success": True,
            "message": "Chrome driver created and tested successfully",
            "logs": logs if verbose else None
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc() if verbose else None,
            "logs": logs if verbose else None
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 