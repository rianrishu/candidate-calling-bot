import os
from dotenv import load_dotenv
from modules.sheets_manager import SheetsManager

def test_sheets_connection():
    try:
        # Load environment variables
        load_dotenv('candidate_calling_bot.env')
        
        # Initialize sheets manager
        sheets_manager = SheetsManager()
        
        # Test reading from the sheet
        print("Testing Google Sheets connection...")
        print(f"Spreadsheet ID: {os.getenv('SPREADSHEET_ID')}")
        
        # Try to get the first row of data
        data = sheets_manager.get_candidates()
        if data:
            print("\nSuccessfully connected to Google Sheets!")
            print("\nFirst row of data:")
            for key, value in data[0].items():
                print(f"{key}: {value}")
        else:
            print("\nConnected to Google Sheets, but no data found.")
            
    except Exception as e:
        print(f"\nError testing Google Sheets connection: {str(e)}")
        raise

if __name__ == "__main__":
    test_sheets_connection() 