import os
import threading 
from flask import Flask, request
import requests
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
transcript_queue = Queue()

AUTH_HEADER = {
    'Authorization': f"App {os.getenv('API_KEY')}",
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
BASE_URL = "https://api.infobip.com/calls/1"

calls_config_id = os.getenv('CALLS_CONFIG_ID')
webhook_url = os.getenv('NGROK_URL')

@app.route('/webhook', methods=['POST'])
def webhook(phone_A):
    ev = request.json
    ev_type = ev.get("type")
    payload = ev.get("payload", {})
    if ev_type == "CALL_ESTABLISHED":
        call_id = payload.get("callId")
        if payload.get("direction") == "OUTBOUND" and payload.get("parentCallId") is None:
            data = {
                "parentCallId": call_id,
                "destination": {
                    "type": "PHONE",
                    "phoneNumber": phone_A
                }
            }
            resp = requests.post(f"{BASE_URL}/calls/{calls_config_id}/calls/call-legs/call/connect-with-new-call", json=data, headers=AUTH_HEADER)

    elif ev_type == "TRANSCRIPTION_RESULT":
        text = payload.get("transcript", {}).get("text", "")
        transcript_queue.put(text)
    return ('', 200)

def start_transcription(call_id):
    url = f"{BASE_URL}/calls/{calls_config_id}/calls/{call_id}/start-transcription"
    data = {"transcription": {"language": "bs-BA", "sendInterimResults": True}}
    requests.post(url, json=data, headers=AUTH_HEADER)

def bridge_call(phone_A, phone_B):
    data = {
        "from": phone_A,
        "to": phone_B,
        "callbackData": "call1"
    }

    resp = requests.post(f"{BASE_URL}/calls/{calls_config_id}/calls", json=data, headers=AUTH_HEADER)
    call = resp.json()
    call_id = call.get("callId")

    return call_id

if __name__ == '__main__':
    threading.Thread(target = lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()