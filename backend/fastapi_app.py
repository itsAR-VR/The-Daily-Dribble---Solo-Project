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
    from .multi_platform_listing_bot import run_from_spreadsheet
except ImportError:
    # Create a dummy function if import fails
    def run_from_spreadsheet(input_path: str, output_path: str) -> None:
        raise RuntimeError("Chrome/Selenium not available. Please check deployment configuration.")

# Test Chrome availability on startup
CHROME_AVAILABLE = True
try:
    from .multi_platform_listing_bot import create_driver
    test_driver = create_driver()
    test_driver.quit()
    print("✅ Chrome driver test successful")
except Exception as e:
    CHROME_AVAILABLE = False
    print(f"❌ Chrome driver test failed: {e}")
    
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
    version="1.0.0"
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
                model="gpt-4",
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
                model="gpt-4",
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
    return {
        "message": "Multi-Platform Listing Bot API",
        "chrome_status": chrome_status,
        "openai_status": openai_status,
        "ai_features": "enabled" if openai_status == "available" else "fallback mode",
        "endpoints": {
            "POST /listings": "Upload Excel file for batch processing",
            "GET /listings/{job_id}": "Get job status and results",
            "POST /listings/single": "Post a single listing",
            "POST /listings/enhanced": "Post with comprehensive data and AI enrichment"
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
            result[platform_field] = " ".join(values)
        else:
            # Direct mapping
            value = getattr(data, data_field, "")
            if isinstance(value, list):
                result[platform_field] = ", ".join(value)
            else:
                result[platform_field] = value
    
    return result


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 