from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

app = Flask(__name__)

# Google Sheets setup
SERVICE_ACCOUNT_FILE = '/etc/secrets/google.json'
SPREADSHEET_ID = '1BohoQznTomfUXVBAKbq4qh6CZJTH36iOquvtI_ADKjA'
RANGE_NAME = 'Sheet1!A:E'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheet_service = build('sheets', 'v4', credentials=credentials)

# Memory to track user progress (basic state management)
user_states = {}
user_data = {}

@app.route("/", methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '').split(':')[-1]
    response = MessagingResponse()
    msg = response.message()

    state = user_states.get(from_number, 'start')

    if state == 'start':
        msg.body("Hey, welcome to Yash Properties, the best real estate dealers in Faridabad! May I know your name?")
        user_states[from_number] = 'name'
    elif state == 'name':
        user_data[from_number] = {'name': incoming_msg}
        msg.body("Thanks! What plot size are you looking for?\nReply with one of the following:\n1. 250 sq. yards\n2. 350 sq. yards\n3. 500 sq. yards \n3Please reply with 1, 2, or 3 to select a plot size.")
        user_states[from_number] = 'size'
    elif state == 'size':
        size_map = {
            '1': '250 sq. yards',
            '2': '350 sq. yards',
            '3': '500 sq. yards'
            
        }
        size = size_map.get(incoming_msg)
        if not size:
            msg.body("Please reply with 1, 2, or 3 to select a plot size.")
            return str(response)

        user_data[from_number]['size'] = size
        user_data[from_number]['number'] = from_number
        user_data[from_number]['date'] = datetime.datetime.now().strftime("%Y-%m-%d")

        # Append to Google Sheet
        values = [[
            '',  # Serial number (Google Sheets formula can auto-increment it)
            user_data[from_number]['date'],
            user_data[from_number]['name'],
            user_data[from_number]['number'],
            user_data[from_number]['size']
        ]]
        body = {'values': values}
        sheet_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        msg.body("Thank you! A member from our team will reach out to you soon.")
        user_states[from_number] = 'done'
    else:
        # Do not respond again to avoid cost
        pass

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
