from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from typing import List, Optional
import mimetypes
from datetime import datetime, timedelta
import glob
from fastapi_utils.tasks import repeat_every
from utils.text_extractor import extract_text
from utils.resume_parser import ResumeParser
from utils.sheets_manager import GoogleSheetsManager

# Google Sheets configuration
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
SHEET_RANGE = 'Sheet1!A:F'  # Adjust based on your sheet structure

# Initialize resume parser
def get_resume_parser():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not found in environment variables"
        )
    return ResumeParser(api_key)

def get_sheets_manager():
    try:
        return GoogleSheetsManager()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Google Sheets manager: {str(e)}"
        )

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
@repeat_every(seconds=60 * 60)  # Run every hour
def scheduled_cleanup() -> None:
    """Run cleanup task periodically"""
    cleanup_old_files()

# Create a temporary directory for file uploads if it doesn't exist
TEMP_UPLOAD_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# File retention period in hours
FILE_RETENTION_HOURS = 24

def cleanup_old_files():
    """Remove temporary files older than FILE_RETENTION_HOURS"""
    cutoff_time = datetime.now() - timedelta(hours=FILE_RETENTION_HOURS)
    
    for file_path in glob.glob(os.path.join(TEMP_UPLOAD_DIR, '*')):
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_modified_time < cutoff_time:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {str(e)}")

# Run cleanup on startup
cleanup_old_files()

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

def is_valid_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.post("/upload_job_description")
async def upload_job_description(description: Optional[str] = None, file: Optional[UploadFile] = None):
    if not description and not file:
        raise HTTPException(status_code=400, detail="Provide either a description or a file.")
    if file:
        # Save and extract text from file
        safe_filename = os.path.basename(file.filename)
        temp_file_path = os.path.join(TEMP_UPLOAD_DIR, safe_filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        extracted_text = extract_text(temp_file_path)
        os.remove(temp_file_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from job description file.")
        JOB_DESCRIPTION["text"] = extracted_text
    else:
        JOB_DESCRIPTION["text"] = description
    return {"message": "Job description uploaded successfully."}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    try:
        uploaded_files = []
        for file in files:
            # Validate file extension
            if not is_valid_file(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} has an invalid extension. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
                )

            # Create a temporary file path with sanitized filename
            safe_filename = os.path.basename(file.filename)
            temp_file_path = os.path.join(TEMP_UPLOAD_DIR, safe_filename)
            
            # Save the file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size and mime type
            file_size = os.path.getsize(temp_file_path)
            mime_type, _ = mimetypes.guess_type(temp_file_path)
            
            # Extract text from the file
            extracted_text = extract_text(temp_file_path)
            
            # Parse resume if text extraction was successful
            resume_data = None
            sheets_status = None
            if extracted_text:
                try:
                    parser = get_resume_parser()
                    resume_data = parser.parse_resume(extracted_text)
                    if resume_data and not isinstance(resume_data, str):
                        # Store resume data in memory for later matching
                        RESUMES.append(resume_data)
                    # Store in Google Sheets if parsing successful
                    if resume_data and not isinstance(resume_data, str) and SPREADSHEET_ID:
                        sheets_manager = get_sheets_manager()
                        sheets_manager.create_sheet_if_not_exists(SPREADSHEET_ID)
                        sheets_status = sheets_manager.append_resume_data(
                            SPREADSHEET_ID,
                            SHEET_RANGE,
                            resume_data
                        )
                except Exception as e:
                    print(f"Error processing resume: {str(e)}")
            
            file_info = {
                "filename": safe_filename,
                "size_bytes": file_size,
                "mime_type": mime_type,
                "extracted_text": extracted_text if extracted_text else "Text extraction failed or unsupported format",
                "parsed_resume": resume_data if resume_data else "Resume parsing failed or no text extracted",
                "sheets_status": sheets_status
            }
            
            # Delete the temporary file after processing
            try:
                os.remove(temp_file_path)
                file_info["cleanup_status"] = "File deleted successfully"
            except Exception as e:
                file_info["cleanup_status"] = f"Failed to delete file: {str(e)}"
            
            uploaded_files.append(file_info)
        
        # After all resumes are uploaded, if job description exists, match resumes
        best_fit_results = []
        if JOB_DESCRIPTION["text"] and RESUMES:
            parser = get_resume_parser()
            for resume in RESUMES:
                try:
                    prompt = f"""Given the following job description and candidate details, determine if the candidate is a strong fit for the role. Respond in JSON with fields: is_best_fit (true/false), reason (string).\n\nJob Description:\n{JOB_DESCRIPTION['text']}\n\nCandidate:\n{resume}\n"""
                    response = parser.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert recruiter."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,
                        max_tokens=500
                    )
                    import json
                    content = response.choices[0].message.content
                    if content.strip().startswith("```json"):
                        content = content.strip().removeprefix("```json").removesuffix("```")
                    elif content.strip().startswith("```"):
                        content = content.strip().removeprefix("```").removesuffix("```")
                    fit_result = json.loads(content)
                    if fit_result.get("is_best_fit"):
                        best_fit_results.append({"resume": resume, "reason": fit_result.get("reason", "")})
                except Exception as e:
                    print(f"Error matching resume: {str(e)}")
            # Write best-fit results to a second sheet
            if best_fit_results and SPREADSHEET_ID:
                sheets_manager = get_sheets_manager()
                # Create second sheet if not exists
                try:
                    sheet_title = "Best Fit Candidates"
                    # Try to add the sheet (ignore if exists)
                    sheets_manager.service.spreadsheets().batchUpdate(
                        spreadsheetId=SPREADSHEET_ID,
                        body={
                            "requests": [
                                {"addSheet": {"properties": {"title": sheet_title}}}
                            ]
                        }
                    ).execute()
                except Exception:
                    pass  # Sheet may already exist
                # Write headers
                sheets_manager.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'{sheet_title}!A1:C1',
                    valueInputOption='USER_ENTERED',
                    body={'values': [['Full Name', 'Email', 'Reason']]}
                ).execute()
                values = [[r["resume"].get("full_name", ""), r["resume"].get("email", ""), r["reason"]] for r in best_fit_results]
                sheets_manager.service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'{sheet_title}!A2',
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body={"values": values}
                ).execute()
        return JSONResponse(
            content={
                "message": "Files uploaded successfully",
                "files": uploaded_files
            },
            status_code=200
        )
    
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
    finally:
        # Make sure to close all file objects
        for file in files:
            file.file.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Resume Parser API"}
# In-memory storage for job description and resumes
JOB_DESCRIPTION = {"text": None}
RESUMES = []