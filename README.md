# Candidate Calling Bot

An automated system that calls job candidates and collects their basic information through a voice-based interview process.

## Features

- Integration with Google Sheets for candidate data management
- Automated voice calls using Twilio
- Speech-to-text processing for candidate responses
- Web interface for managing calls
- Automatic response recording and summary generation
- Status tracking for each candidate

## Prerequisites

1. Python 3.8 or higher
2. Google Cloud Platform account with Sheets API enabled
3. Twilio account with voice capabilities
4. A Google Sheet with the following columns:
   - Freshteam ID
   - Name
   - Phone
   - Role ID
   - JD Link
   - Status

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip3 install -r requirements.txt
```

4. Set up your environment variables by copying the example file:
```bash
cp .env.example .env
```

5. Configure your environment variables in the `.env` file:
```
# Google Sheets API credentials
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=your_spreadsheet_id_here

# Twilio credentials
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Application settings
FLASK_SECRET_KEY=your_secret_key_here
RECORDINGS_PATH=./recordings
```

6. Set up Google Sheets API:
   - Go to Google Cloud Console
   - Enable Google Sheets API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials and save as `credentials.json`

## Usage

1. Start the Flask application:
```bash
python3 app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. The interface will display all candidates from your Google Sheet

4. Select the candidates you want to call and click "Start Calling"

5. The system will:
   - Call each candidate
   - Ask for consent to record
   - Conduct the interview
   - Save responses to Google Sheets
   - Update call status

## Call Flow

1. Introduction and consent
2. Questions asked:
   - Current workplace
   - Notice period
   - Potential joining date
   - Motivation to join Nuclei
   - Current/last salary
   - Variable component details
   - Expected salary

## Response Handling

- All responses are processed using speech-to-text
- Responses are saved in the Google Sheet
- A summary is generated for each completed call
- Call recordings are stored (if enabled)

## Troubleshooting

1. If calls aren't connecting:
   - Check Twilio credentials
   - Verify phone number format (should be E.164)
   - Check Twilio account balance

2. If responses aren't saving:
   - Verify Google Sheets API credentials
   - Check spreadsheet permissions
   - Verify spreadsheet ID

3. If web interface isn't loading:
   - Check Flask server logs
   - Verify network connectivity
   - Clear browser cache

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 