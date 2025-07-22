#!/usr/bin/env python3
"""FastAPI backend for the multi-platform listing bot.

This FastAPI application wraps the multi-platform listing bot script,
providing HTTP endpoints to submit Excel files and retrieve results.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import sys
from pathlib import Path

# Add parent directory to Python path to import the main script
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the main script - handle different deployment scenarios
try:
    from multi_platform_listing_bot import run_from_spreadsheet
except ImportError:
    # If in backend directory, try importing from parent
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from multi_platform_listing_bot import run_from_spreadsheet

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


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "Multi-Platform Listing Bot API is running"}


@app.post("/listings", status_code=201)
async def create_listing(file: UploadFile = File(...)):
    """Accept an uploaded Excel file, process it, and return a job ID.
    
    The file should contain columns for:
    - platform: The marketplace platform (hubx, gsmexchange, kardof, cellpex, handlot, linkedin)
    - product_name: Name of the product
    - condition: Product condition
    - quantity: Number of items
    - price: Price per item
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Save the uploaded file
    input_path = os.path.join(JOBS_DIR, f"{job_id}_input.xlsx")
    output_path = os.path.join(JOBS_DIR, f"{job_id}_output.xlsx")
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Run the automation synchronously
        # Note: In production, consider using background tasks for better performance
        run_from_spreadsheet(input_path, output_path)
        
        return {
            "job_id": job_id,
            "message": "Listings processed successfully",
            "status": "completed"
        }
        
    except Exception as exc:
        # Clean up input file on error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")


@app.get("/listings/{job_id}")
def get_listing(job_id: str):
    """Return the processed Excel file for a given job ID, if it exists."""
    output_path = os.path.join(JOBS_DIR, f"{job_id}_output.xlsx")
    
    if not os.path.isfile(output_path):
        # Check if input file exists (job was submitted but failed)
        input_path = os.path.join(JOBS_DIR, f"{job_id}_input.xlsx")
        if os.path.isfile(input_path):
            raise HTTPException(status_code=500, detail="Job failed during processing")
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    
    # Serve the completed Excel file back to the caller
    return FileResponse(
        path=output_path,
        filename=f"listings_results_{job_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/listings/{job_id}/status")
def get_listing_status(job_id: str):
    """Get the status of a listing job without downloading the file."""
    output_path = os.path.join(JOBS_DIR, f"{job_id}_output.xlsx")
    input_path = os.path.join(JOBS_DIR, f"{job_id}_input.xlsx")
    
    if os.path.isfile(output_path):
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Results are ready for download"
        }
    elif os.path.isfile(input_path):
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Job is currently being processed"
        }
    else:
        raise HTTPException(status_code=404, detail="Job not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 