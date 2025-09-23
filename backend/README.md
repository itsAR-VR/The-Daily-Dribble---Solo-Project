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

# Gmail OAuth for 2FA code retrieval (optional)
GMAIL_CLIENT_ID=your-google-client-id
GMAIL_CLIENT_SECRET=your-google-client-secret
GMAIL_REFRESH_TOKEN=your-google-refresh-token
GMAIL_TARGET_EMAIL=your-email@gmail.com
GMAIL_TOKEN_FILE=./data/gmail_token.pickle

# OpenAI API for AI-enhanced descriptions (optional)
OPENAI_API_KEY=your_openai_api_key
```

### Gmail OAuth Setup (Optional – automatic 2FA retrieval)

The bot can automatically retrieve 2FA verification codes from Gmail using OAuth. Once you complete the flow the refresh token keeps the integration signed in so you do not need to re-authorize each run.

1. **Create a Google Cloud project** or reuse an existing one.
2. **Enable the Gmail API** under *APIs & Services → Library*.
3. **Configure the OAuth consent screen** (External type is fine for individual use).
4. **Create OAuth client credentials** → choose *Desktop app* and note the Client ID/Secret.
5. Run the helper to complete OAuth locally and grab a refresh token:
   ```bash
   python backend/get_refresh_token.py
   ```
6. Copy the values into your environment:
   ```bash
   GMAIL_CLIENT_ID=your-google-client-id
   GMAIL_CLIENT_SECRET=your-google-client-secret
   GMAIL_REFRESH_TOKEN=the-refresh-token-you-just-generated
   GMAIL_TARGET_EMAIL=your-email@gmail.com
   GMAIL_TOKEN_FILE=./data/gmail_token.pickle  # optional override
   ```
7. **Persist the token file**. The backend caches the live access token at `GMAIL_TOKEN_FILE` (defaults to `./data/gmail_token.pickle`). Mount or retain that directory (`DATA_DIR`/`./data`) in production so the session stays warm.

If you ever need to rotate credentials, delete the token file and rerun the helper to generate a new refresh token.

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

### Manual 2FA Assistance
When Gmail-based retrieval is unavailable, the backend exposes manual endpoints:

```
POST /manual-2fa/{job_id}
GET /manual-2fa/{job_id}
DELETE /manual-2fa/{job_id}
```

Workflow:
1. Start an enhanced visual job (`POST /listings/enhanced-visual/start`) and capture the returned `job_id`.
2. When the marketplace prompts for a verification code, submit it via `POST /manual-2fa/{job_id}` with `{"code": "123456"}`.
3. Poll `GET /manual-2fa/{job_id}` until it reports `submitted`; the automation flow will resume automatically.
4. Optionally call `DELETE /manual-2fa/{job_id}` after completion to clear stored codes.

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
