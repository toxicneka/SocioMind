import gspread
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_ID, GOOGLE_SHEETS_CREDS
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def init_google_sheets():
    creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDS, scopes=SCOPES)
    return gspread.authorize(creds)

def save_to_sheets(gc, user_data: dict):
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.get_worksheet(0)
        worksheet.append_row([
            user_data['user_id'],
            user_data['username'],
            user_data['personality_type'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")
        raise