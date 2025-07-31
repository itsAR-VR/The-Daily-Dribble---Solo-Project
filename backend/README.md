# Multi-Platform Listing Bot API

This FastAPI backend wraps the multi-platform listing bot script, providing HTTP endpoints to submit Excel files and retrieve results.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables for each platform you want to use:
```bash
# Create a .env file in the root directory with your credentials
HUBX_USERNAME=your_hubx_username
HUBX_PASSWORD=your_hubx_password

GSMEXCHANGE_USERNAME=your_gsmexchange_username
GSMEXCHANGE_PASSWORD=your_gsmexchange_password

KARDOF_USERNAME=your_kardof_username
KARDOF_PASSWORD=your_kardof_password

CELLPEX_USERNAME=your_cellpex_username
CELLPEX_PASSWORD=your_cellpex_password

HANDLOT_USERNAME=your_handlot_username
HANDLOT_PASSWORD=your_handlot_password

LINKEDIN_USERNAME=your_linkedin_username
LINKEDIN_PASSWORD=your_linkedin_password

# Gmail API for 2FA code retrieval (optional)
GMAIL_TARGET_EMAIL=your-email@gmail.com
GMAIL_SERVICE_ACCOUNT_JSON='{"type": "service_account", "project_id": "...", ...}'

# OpenAI API for AI-enhanced descriptions (optional)
OPENAI_API_KEY=your_openai_api_key
```

### Gmail API Setup (Optional - for automatic 2FA handling)

The bot can automatically retrieve 2FA verification codes from Gmail for platforms that require them (like GSM Exchange and Cellpex). To enable this:

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one

2. **Enable Gmail API**:
   - Go to APIs & Services > Library
   - Search for "Gmail API" and enable it

3. **Create Service Account**:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "Service Account"
   - Download the JSON key file

4. **Enable Domain-Wide Delegation**:
   - In the service account settings, enable "G Suite Domain-wide Delegation"
   - Note the Client ID

5. **Authorize Service Account** (for Google Workspace):
   - Go to Google Admin Console > Security > API Controls > Domain-wide Delegation
   - Add the Client ID and scope: `https://www.googleapis.com/auth/gmail.send`

6. **Set Environment Variables**:
   ```bash
   GMAIL_TARGET_EMAIL=your-email@gmail.com
   GMAIL_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'  # Full JSON content
   ```

7. **Test Configuration**:
   ```bash
   python setup_gmail_env_template.py
   ```

## Running the Server

Start the FastAPI server:
```bash
python fastapi_app.py
```

Or using uvicorn directly:
```bash
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
```
GET /
```
Returns a simple health check message.

### Submit Listings
```
POST /listings
```
Upload an Excel file with product listings to be processed across multiple platforms.

**Request:**
- File upload (multipart/form-data)
- File must be `.xlsx` or `.xls` format

**Required Excel Columns:**
- `platform`: Platform name (hubx, gsmexchange, kardof, cellpex, handlot, linkedin)
- `product_name`: Name of the product
- `condition`: Product condition
- `quantity`: Number of items
- `price`: Price per item

**Response:**
```json
{
  "job_id": "uuid-string",
  "message": "Listings processed successfully",
  "status": "completed"
}
```

### Get Results
```
GET /listings/{job_id}
```
Download the processed Excel file with results.

**Response:**
- Returns the Excel file with a `Status` column added showing success/error for each row

### Check Status
```
GET /listings/{job_id}/status
```
Check the status of a job without downloading the file.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "message": "Results are ready for download"
}
```

## Example Usage

1. Upload a listings file:
```bash
curl -X POST "http://localhost:8000/listings" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_listings.xlsx"
```

2. Download results:
```bash
curl -X GET "http://localhost:8000/listings/{job_id}" \
  -H "accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  --output results.xlsx
```

## Deployment

For production deployment, consider:
- Using environment variables for configuration
- Setting up proper CORS origins
- Using background tasks for long-running processing
- Adding authentication/authorization
- Using a process manager like PM2 or systemd
- Setting up reverse proxy with nginx

## Supported Platforms

- Hubx
- GSMExchange  
- Kardof
- Cellpex
- Handlot
- LinkedIn

Each platform requires valid credentials set in environment variables. 

==> Using Python version: 3.10.5