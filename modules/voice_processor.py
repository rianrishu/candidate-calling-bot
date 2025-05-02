import os
from twilio.twiml.voice_response import VoiceResponse
from .call_handler import CallHandler

class VoiceProcessor:
    def __init__(self):
        self.call_handler = CallHandler()
        self.responses = {}
        print("Initialized VoiceProcessor")

    def handle_incoming_call(self, request):
        """Handle incoming Twilio voice call."""
        try:
            print(f"Handling incoming call: {request.form}")
            print(f"Request args: {request.args}")
            print(f"Request headers: {request.headers}")
            
            # Get candidate_id from either args or form
            candidate_id = request.args.get('candidate_id') or request.form.get('candidate_id')
            print(f"Candidate ID from request: {candidate_id}")
            
            if not candidate_id:
                print("Warning: No candidate_id provided in request")
                response = VoiceResponse()
                response.say("I'm sorry, there was an error with the call setup. Please try again later.", voice='Polly.Raveena')
                response.hangup()
                return str(response)
                
            twiml = self.call_handler.create_initial_twiml(candidate_id)
            print(f"Generated TwiML: {twiml}")
            return twiml
        except Exception as e:
            print(f"Error in handle_incoming_call: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            response = VoiceResponse()
            response.say("I'm sorry, there was an error processing your call. Please try again later.", voice='Polly.Raveena')
            response.hangup()
            return str(response)

    def process_response(self, request):
        """Process gathered voice response."""
        try:
            print(f"Processing response: {request.form}")
            candidate_id = request.args.get('candidate_id')
            question_number = int(request.args.get('question', 0))
            print(f"Candidate ID: {candidate_id}, Question number: {question_number}")
            
            if question_number == 0:  # Initial consent
                speech_result = request.form.get('SpeechResult', None)
                print(f"Consent speech result: {speech_result}")
                if not speech_result:
                    # If no speech received, repeat the initial message
                    return self.call_handler.create_initial_twiml(candidate_id)
                return self.call_handler.handle_consent(speech_result, candidate_id)
            
            # Process speech response
            speech_result = request.form.get('SpeechResult')
            print(f"Speech result: {speech_result}")
            
            if speech_result:
                if candidate_id not in self.responses:
                    self.responses[candidate_id] = {}
                
                # Map question number to response field
                response_mapping = {
                    1: 'current_company',
                    2: 'joining_date_current_company',
                    3: 'notice_period',
                    4: 'current_salary',
                    5: 'variable_component',
                    6: 'expected_salary'
                }
                
                if question_number in response_mapping:
                    self.responses[candidate_id][response_mapping[question_number]] = speech_result
                    print(f"Saved response for {response_mapping[question_number]}: {speech_result}")
                
                # If this was the last question, save all responses
                if question_number == 6:
                    print(f"Saving all responses for candidate {candidate_id}")
                    self.save_responses(candidate_id)
            
            # Move to next question
            return self.call_handler.ask_next_question(VoiceResponse(), question_number + 1, candidate_id)
            
        except Exception as e:
            print(f"Error processing response: {str(e)}")
            # If there's an error, try to continue with the next question
            response = VoiceResponse()
            response.say("I'm sorry, I didn't catch that. Let's move on to the next question.", voice='Polly.Raveena')
            return str(self.call_handler.ask_next_question(response, question_number + 1, candidate_id))

    def save_responses(self, candidate_id):
        """Save the gathered responses to Google Sheets."""
        try:
            print(f"Saving responses for candidate {candidate_id}")
            from .sheets_manager import SheetsManager
            sheets_manager = SheetsManager()
            
            # Create a summary of the call
            responses = self.responses.get(candidate_id, {})
            summary = (
                f"Current Company: {responses.get('current_company', 'N/A')}\n"
                f"Joining Date (Current Company): {responses.get('joining_date_current_company', 'N/A')}\n"
                f"Notice Period: {responses.get('notice_period', 'N/A')}\n"
                f"Current Salary: {responses.get('current_salary', 'N/A')}\n"
                f"Variable Component: {responses.get('variable_component', 'N/A')}\n"
                f"Expected Salary: {responses.get('expected_salary', 'N/A')}"
            )
            
            print(f"Call summary: {summary}")
            
            responses['call_summary'] = summary
            sheets_manager.update_candidate_status(candidate_id, 'completed', responses)
            print(f"Updated candidate {candidate_id} status to completed")
            
            # Clear responses for this candidate
            if candidate_id in self.responses:
                del self.responses[candidate_id]
                
        except Exception as e:
            print(f"Error saving responses: {str(e)}")
            raise 