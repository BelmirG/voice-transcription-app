import os
import threading 
from flask import Flask, request
import requests
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
transcript_queue = Queue()
status_queue = Queue()

AUTH_HEADER = {
    'Authorization': f"App {os.getenv('API_KEY')}",
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
BASE_URL = "https://api.infobip.com/calls/1"

calls_config_id = os.getenv('CALLS_CONFIG_ID')
webhook_url = os.getenv('NGROK_URL')

@app.route('/webhook', methods=['POST'])
def webhook():
    ev = request.json
    ev_type = ev.get("type")
    payload = ev.get("payload", {})
    call_id = payload.get("callId")

    if ev_type == "CALL RINGING":
        status_queue.put("Ringing...")
    elif ev_type == "CALL ESTABLISHED":
        status_queue.put("Call connected")
        start_transcription(call_id)
    elif ev_type == "CALL FINISHED":
        status_queue.put("Call ended")
    elif ev_type == "CALL FAILED":
        status_queue.put("Call failed")
    elif ev_type == "TRANSCRIPTION_RESULT":
        text = payload.get("transcript", {}).get ("text", "")
        if text:
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
    resp = requests.post(f"{BASE_URL}/{calls_config_id}/calls", json=data, headers=AUTH_HEADER)
    return resp.json().get("callId")

if __name__ == '__main__':
    threading.Thread(target = lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()