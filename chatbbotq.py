import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

app = Flask(__name__)

# Handle both Render and local paths
SERVICE_ACCOUNT_FILE = '/etc/secrets/google.json'
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    SERVICE_ACCOUNT_FILE = r'C:\chatbot\google.json'

SPREADSHEET_ID = '1BohoQznTomfUXVBAKbq4qh6CZJTH36iOquvtI_ADKjA'
RANGE_NAME = 'Sheet1!A:E'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheet_service = build('sheets', 'v4', credentials=credentials)

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
        msg.body("Hey, welcome to Yash Properties! May I know your name?")
        user_states[from_number] = 'name'
    elif state == 'name':
        user_data[from_number] = {'name': incoming_msg}
        msg.body("Thanks! What plot size are you looking for?\nReply with:\n1. 250\n2. 350\n3. 500\n4. please reply with 1 or 2 or 3")
        user_states[from_number] = 'size'
    elif state == 'size':
        size_map = {'1': '250 sq. yards', '2': '350 sq. yards', '3': '500 sq. yards'}
        size = size_map.get(incoming_msg)
        if not size:
            msg.body("Please reply with 1, 2, or 3.")
            return str(response)

        user_data[from_number]['size'] = size
        user_data[from_number]['number'] = from_number
        user_data[from_number]['date'] = datetime.datetime.now().strftime("%Y-%m-%d")

        values = [[
            '',  # Serial No.
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

        msg.body("Thanks! Our team will reach out to you soon.")
        user_states[from_number] = 'done'

    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
