import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from modules.sheets_manager import SheetsManager
from modules.call_handler import CallHandler
from modules.voice_processor import VoiceProcessor

# Load environment variables
load_dotenv('candidate_calling_bot.env')

# Debug: Print environment variables
print("Environment Variables:")
print(f"TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID')}")
print(f"TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN')}")
print(f"TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER')}")
print(f"SPREADSHEET_ID: {os.getenv('SPREADSHEET_ID')}")
print(f"NGROK_URL: {os.getenv('NGROK_URL')}")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Initialize components
sheets_manager = SheetsManager()
call_handler = CallHandler()
voice_processor = VoiceProcessor()

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/fetch-candidates', methods=['GET'])
def fetch_candidates():
    """Fetch candidates from Google Sheet."""
    try:
        candidates = sheets_manager.get_candidates()
        return jsonify({'success': True, 'candidates': candidates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/initiate-calls', methods=['POST'])
def initiate_calls():
    """Start the calling process for selected candidates."""
    try:
        candidate_ids = request.json.get('candidate_ids', [])
        results = call_handler.schedule_calls(candidate_ids)
        return jsonify({
            'success': True,
            'message': 'Calls initiated successfully',
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/voice', methods=['POST'])
def voice():
    """Handle incoming voice calls."""
    return str(voice_processor.handle_incoming_call(request))

@app.route('/gather', methods=['POST'])
def gather():
    """Handle gathered voice input."""
    return str(voice_processor.process_response(request))

@app.route('/call-status', methods=['POST'])
def call_status():
    """Handle call status updates."""
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        candidate_id = request.args.get('candidate_id')
        
        print(f"Call Status Update - CallSid: {call_sid}, Status: {call_status}, Candidate ID: {candidate_id}")
        
        if not candidate_id:
            print(f"Warning: No candidate_id found in request for CallSid: {call_sid}")
            return '', 200
        
        # Update candidate status in sheets
        status_mapping = {
            'initiated': 'calling',
            'ringing': 'calling',
            'answered': 'in_progress',
            'completed': 'completed',
            'failed': 'failed',
            'busy': 'busy',
            'no-answer': 'no_answer',
            'no_answer': 'no_answer',  # Handle both formats
            'canceled': 'canceled',
            'rejected': 'rejected',
            'declined': 'rejected',
            'disconnected': 'disconnected'
        }
        
        new_status = status_mapping.get(call_status.lower(), 'unknown')
        print(f"Updating candidate {candidate_id} status to {new_status}")
        
        # Add additional data for various call outcomes
        additional_data = None
        if new_status in ['no_answer', 'busy', 'failed', 'canceled', 'rejected', 'disconnected']:
            additional_data = {
                'reason': call_status.lower(),
                'timestamp': request.form.get('Timestamp'),
                'call_sid': call_sid,
                'call_duration': request.form.get('CallDuration', '0'),
                'answered_by': request.form.get('AnsweredBy', 'unknown')
            }
            print(f"Additional data for {candidate_id}: {additional_data}")
        
        # Update the status in sheets
        sheets_manager.update_candidate_status(candidate_id, new_status, additional_data)
        print(f"Successfully updated status for candidate {candidate_id}")
        
        return '', 200
    except Exception as e:
        print(f"Error handling call status: {str(e)}")
        return '', 500

@app.route('/recording-status', methods=['POST'])
def recording_status():
    """Handle recording status updates."""
    try:
        recording_sid = request.form.get('RecordingSid')
        recording_status = request.form.get('RecordingStatus')
        recording_url = request.form.get('RecordingUrl')
        call_sid = request.form.get('CallSid')
        
        if recording_status == 'completed' and recording_url:
            # Store recording URL in sheets
            # This would be implemented based on your data structure
            pass
        
        return '', 200
    except Exception as e:
        print(f"Error handling recording status: {str(e)}")
        return '', 500

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=True
    ) 