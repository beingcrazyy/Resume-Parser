# Resume Parser API

A FastAPI-based service that extracts and parses information from resume files (PDF/DOCX) using OpenAI's GPT model.

## Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix/MacOS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up API keys and credentials:

   a. OpenAI API Key:
      - Get your API key from [OpenAI](https://platform.openai.com/api-keys)
      - Set it as an environment variable:
        ```bash
        # On Windows
        set OPENAI_API_KEY=your-api-key-here
        
        # On Unix/MacOS
        export OPENAI_API_KEY=your-api-key-here
        ```

   b. Google Sheets Integration:
      - Create a Google Cloud Project
      - Enable Google Sheets API
      - Create a service account and download credentials JSON
      - Share your Google Sheet with the service account email
      - Set environment variables:
        ```bash
        # On Windows
        set GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
        set GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
        
        # On Unix/MacOS
        export GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
        export GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
        ```

## Running the Server

Start the server using uvicorn:
```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### Upload Files
- **URL**: `/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Request Body**: Multiple files (PDF/DOCX)
- **Response**: JSON containing:
  - File metadata (name, size, mime type)
  - Extracted text content
  - Parsed resume information:
    - Full Name
    - Email Address
    - Phone Number
    - Skills
    - Work Experience
    - Education

### Root Endpoint
- **URL**: `/`
- **Method**: `GET`
- Returns a welcome message

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`