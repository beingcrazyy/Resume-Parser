from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Dict, Any, List, Optional
import os

class GoogleSheetsManager:
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Google Sheets manager with service account credentials.

        Args:
            credentials_path (Optional[str]): Path to service account JSON file.
                If not provided, will try to get from environment variable.
        """
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not self.credentials_path:
            raise ValueError("Google Sheets credentials must be provided or set in GOOGLE_SHEETS_CREDENTIALS environment variable")

        # Initialize credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        # Build service
        self.service = build('sheets', 'v4', credentials=self.credentials)

    def append_resume_data(self, spreadsheet_id: str, range_name: str, resume_data: Dict[str, Any]) -> bool:
        """Append resume data to Google Sheet.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet to append data to
            range_name (str): The A1 notation of the range to append data to
            resume_data (Dict[str, Any]): Parsed resume data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format data for sheet
            row_data = [
                resume_data.get('full_name', ''),
                resume_data.get('email', ''),
                resume_data.get('phone', ''),
                ', '.join(resume_data.get('skills', [])),
                # Join work experience into a single cell
                '\n'.join(
                    f"{exp.get('company', '')} - {exp.get('position', '')} ({exp.get('duration', '')})" 
                    for exp in resume_data.get('work_experience', [])
                ),
                # Join education into a single cell
                '\n'.join(
                    f"{edu.get('institution', '')} - {edu.get('degree', '')} ({edu.get('graduation_year', '')})" 
                    for edu in resume_data.get('education', [])
                )
            ]

            body = {
                'values': [row_data]
            }

            # Append the data
            self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            return True

        except Exception as e:
            print(f"Error appending data to Google Sheet: {str(e)}")
            return False

    def create_sheet_if_not_exists(self, spreadsheet_id: str) -> None:
        """Create sheet with headers if it doesn't exist.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet
        """
        try:
            headers = [
                ['Full Name', 'Email', 'Phone', 'Skills', 'Work Experience', 'Education']
            ]

            # Check if sheet is empty
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A1:F1'
            ).execute()

            # If empty, add headers
            if 'values' not in result:
                body = {
                    'values': headers
                }
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='A1:F1',
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()

        except Exception as e:
            print(f"Error checking/creating sheet: {str(e)}")