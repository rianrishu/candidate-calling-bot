import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

class SheetsManager:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self):
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.credentials = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        creds = None
        
        # Load credentials from token.pickle if it exists
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials are not valid, refresh or create new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE'), self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        self.service = build('sheets', 'v4', credentials=creds)
    
    def get_candidates(self):
        """Get all candidates from the spreadsheet."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A2:G'
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # Convert to list of dictionaries
            candidates = []
            for row in values:
                if len(row) >= 7:  # Ensure we have all required fields
                    candidate = {
                        'candidate_id': row[0],
                        'freshteam_id': row[1],
                        'name': row[2],
                        'phone': row[3],
                        'role_id': row[4],
                        'jd_link': row[5],
                        'status': row[6] if len(row) > 6 else 'pending'
                    }
                    candidates.append(candidate)
            
            return candidates
        except Exception as e:
            print(f"Error fetching candidates: {str(e)}")
            raise
    
    def get_candidate_by_id(self, candidate_id):
        """Get a specific candidate by their Candidate ID."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A2:G'
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
            
            # Find the candidate with matching ID
            for row in values:
                if len(row) >= 7 and row[0] == candidate_id:
                    return {
                        'candidate_id': row[0],
                        'freshteam_id': row[1],
                        'name': row[2],
                        'phone': row[3],
                        'role_id': row[4],
                        'jd_link': row[5],
                        'status': row[6] if len(row) > 6 else 'pending'
                    }
            
            return None
        except Exception as e:
            print(f"Error fetching candidate: {str(e)}")
            raise
    
    def update_candidate_status(self, candidate_id, new_status, additional_data=None):
        """Update a candidate's status and additional data in the spreadsheet."""
        try:
            # Find the row number for the candidate
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A2:A'
            ).execute()
            
            values = result.get('values', [])
            if not values:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Find the row number (1-based index)
            row_number = None
            for i, row in enumerate(values, start=2):  # Start from row 2
                if row and row[0] == candidate_id:
                    row_number = i
                    break
            
            if not row_number:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Prepare the update data
            update_data = [new_status]  # Status in column G
            
            # Add additional data if provided
            if additional_data:
                if isinstance(additional_data, dict):
                    # Extract individual fields from additional_data
                    current_company = additional_data.get('current_company', '')
                    joining_date = additional_data.get('joining_date_current_company', '')
                    notice_period = additional_data.get('notice_period', '')
                    current_salary = additional_data.get('current_salary', '')
                    variable_component = additional_data.get('variable_component', '')
                    expected_salary = additional_data.get('expected_salary', '')
                    call_summary = additional_data.get('call_summary', '')
                    
                    # Add each field to update_data
                    update_data.extend([
                        current_company,      # Column H
                        joining_date,        # Column I
                        notice_period,       # Column J
                        current_salary,      # Column K
                        variable_component,  # Column L
                        expected_salary,     # Column M
                        call_summary         # Column N
                    ])
            
            # Update the status column (G) and additional data columns (H through N)
            range_name = f'Sheet1!G{row_number}'
            if len(update_data) > 1:
                range_name = f'Sheet1!G{row_number}:N{row_number}'
            
            body = {
                'values': [update_data]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error updating candidate status: {str(e)}")
            raise 