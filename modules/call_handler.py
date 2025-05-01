import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from .sheets_manager import SheetsManager

class CallHandler:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.ngrok_url = os.getenv('NGROK_URL', 'http://localhost:5001')
        self.client = Client(self.account_sid, self.auth_token)
        self.sheets_manager = SheetsManager()
        print(f"Initialized CallHandler with ngrok_url: {self.ngrok_url}")

    def format_phone_number(self, phone):
        """Format phone number to E.164 format for Indian numbers."""
        # Remove any spaces or special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # If number starts with 0, remove it
        if phone.startswith('0'):
            phone = phone[1:]
            
        # If number is 10 digits, add +91
        if len(phone) == 10:
            return f"+91{phone}"
            
        # If number already has country code (11 or 12 digits), add +
        if len(phone) in [11, 12]:
            return f"+{phone}"
            
        # If number is already in E.164 format, return as is
        if phone.startswith('+'):
            return phone
            
        # Default case: assume it's a 10-digit number and add +91
        return f"+91{phone}"

    def schedule_calls(self, candidate_ids):
        """Schedule calls for the selected candidates."""
        results = []
        for candidate_id in candidate_ids:
            try:
                call_sid = self.initiate_call(candidate_id)
                results.append({
                    'candidate_id': candidate_id,
                    'status': 'success',
                    'call_sid': call_sid
                })
            except Exception as e:
                print(f"Error in schedule_calls for {candidate_id}: {str(e)}")
                results.append({
                    'candidate_id': candidate_id,
                    'status': 'error',
                    'error': str(e)
                })
        return results

    def initiate_call(self, candidate_id):
        """Initiate a call to a candidate."""
        try:
            print(f"Getting candidate details for ID: {candidate_id}")
            # Get candidate details from sheets_manager
            candidate = self.sheets_manager.get_candidate_by_id(candidate_id)
            if not candidate:
                raise ValueError(f"Candidate with ID {candidate_id} not found")
            
            print(f"Found candidate: {candidate}")
            candidate_phone = candidate.get('phone')
            if not candidate_phone:
                raise ValueError(f"No phone number found for candidate {candidate_id}")
            
            # Format phone number to E.164 format
            formatted_phone = self.format_phone_number(candidate_phone)
            print(f"Original phone: {candidate_phone}, Formatted phone: {formatted_phone}")
            
            # Create the call
            call_url = f'{self.ngrok_url}/voice?candidate_id={candidate_id}'
            print(f"Creating call with URL: {call_url}")
            
            call = self.client.calls.create(
                url=call_url,
                to=formatted_phone,
                from_=self.phone_number,
                record=True,
                recording_status_callback=f'{self.ngrok_url}/recording-status',
                status_callback=f'{self.ngrok_url}/call-status',
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            
            print(f"Call created with SID: {call.sid}")
            
            # Update candidate status in sheets
            self.sheets_manager.update_candidate_status(candidate_id, 'calling')
            
            return call.sid
        except Exception as e:
            print(f"Error initiating call: {str(e)}")
            # Update candidate status to error
            self.sheets_manager.update_candidate_status(candidate_id, 'error', {'error': str(e)})
            raise

    def create_initial_twiml(self, candidate_id=None):
        """Create initial TwiML for the call."""
        try:
            print("Creating initial TwiML")
            response = VoiceResponse()
            
            # Add a pause to ensure the call is connected
            response.pause(length=1)
            
            initial_message = (
                "Hello! I'm calling from Nuclei regarding your job application. "
                "This call will be recorded for quality purposes. "
                "Do you consent to proceed with the interview? Press 1 for yes, or 2 for no."
            )
            print(f"Initial message: {initial_message}")
            
            response.say(initial_message, voice='Polly.Raveena')
            
            # Create gather with absolute URL and candidate_id
            gather_url = f'{self.ngrok_url}/gather'
            if candidate_id:
                gather_url += f'?candidate_id={candidate_id}'
            
            gather = Gather(
                num_digits=1,
                action=gather_url,
                method='POST',
                timeout=10,
                speech_timeout='auto'
            )
            print("Created Gather verb")
            response.append(gather)
            
            # If no input is received, repeat the message with absolute URL and candidate_id
            redirect_url = f'{self.ngrok_url}/voice'
            if candidate_id:
                redirect_url += f'?candidate_id={candidate_id}'
            response.redirect(redirect_url)
            
            twiml = str(response)
            print(f"Generated TwiML: {twiml}")
            return twiml
        except Exception as e:
            print(f"Error creating initial TwiML: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def handle_consent(self, digits, candidate_id=None):
        """Handle the candidate's consent response."""
        print(f"Handling consent with digits: {digits}, candidate_id: {candidate_id}")
        response = VoiceResponse()
        
        if digits == '1':
            response.say(
                "Thank you. I'll now ask you a series of questions about your "
                "application. Please answer each question after the beep.",
                voice='Polly.Raveena'
            )
            return str(self.ask_next_question(response, 1, candidate_id))
        else:
            response.say(
                "Thank you for your time. We respect your decision. Have a great day!",
                voice='Polly.Raveena'
            )
            response.hangup()
        
        return str(response)

    def ask_next_question(self, response, question_number, candidate_id=None):
        """Ask the next question in the sequence."""
        print(f"Asking question number: {question_number}")
        questions = {
            1: "Where are you currently working?",
            2: "What is your notice period?",
            3: "By when can you join us?",
            4: "Why do you want to join Nuclei?",
            5: "What is your current or last drawn annual salary?",
            6: "Is there a variable component in your salary?",
            7: "What is your expected salary?"
        }
        
        if question_number <= len(questions):
            response.say(questions[question_number], voice='Polly.Raveena')
            
            # Create gather URL with candidate_id
            gather_url = f'{self.ngrok_url}/gather'
            if candidate_id:
                gather_url += f'?candidate_id={candidate_id}&question={question_number}'
            else:
                gather_url += f'?question={question_number}'
                
            gather = Gather(
                input='speech',
                action=gather_url,
                method='POST',
                language='en-IN',
                timeout=10,
                speech_timeout='auto'
            )
            response.append(gather)
            
            # If no input is received, repeat the question with candidate_id
            redirect_url = f'{self.ngrok_url}/voice'
            if candidate_id:
                redirect_url += f'?candidate_id={candidate_id}&question={question_number}'
            else:
                redirect_url += f'?question={question_number}'
            response.redirect(redirect_url)
        else:
            response.say(
                "Thank you for providing all the information. If shortlisted, "
                "someone from our team will reach out to you soon. Have a great day!",
                voice='Polly.Raveena'
            )
            response.hangup()
        
        return str(response) 