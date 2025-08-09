from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
import os
import threading
from webhook_server import transcript_queue, bridge_call, start_transcription
import requests
import http.client
import json
import time
from dotenv import load_dotenv

load_dotenv()

class VoiceApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transcript = "Waiting for transcription..."
        self.call_id = None

    def build(self):
        layout = BoxLayout(orientation = 'vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='VoiceApp: Call Transcription'))
        self.inputA = TextInput(hint_text='Phone Number A')
        self.inputB = TextInput(hint_text='Phone Number B')
        layout.add_widget(self.inputA)
        layout.add_widget(self.inputB)
        self.status = Label(text='Waiting...', size_hint=(1, 0.5))
        layout.add_widget(Button(text='Start Call', on_press=self.initiate_call))
        layout.add_widget(self.status)
        return layout

    def initiate_call(self, instance):
        import webhook_server
        webhook_server.calls_config_id = os.getenv('CALLS_CONFIG_ID')
        webhook_server.AUTH_HEADER["Authorization"] = f"App {os.getenv('API_KEY')}"
        webhook_server.BASE_URL = "https://api.infobip.com/calls/1"
        
        phone_A = self.inputA.text.strip()
        phone_B = self.inputB.text.strip()
        def bridge_ui():
            return webhook_server.bridge_call(phone_A, phone_B)
        
        webhook_server.bridge_call = bridge_ui

        threading.Thread(target=self.call_flow, daemon=True).start()
        threading.Thread(target=self.poll_transcript, daemon=True).start()

    def call_flow(self):
        call_id = bridge_call()
        time.sleep(2)
        start_transcription(call_id)

    def poll_transcript(self):
        while True:
            try:
                text = transcript_queue.get(timeout=120)
                self.status.text = text
            except:
                self.status.text = "Transcription timeout or it ended."
                break 

if __name__ == '__main__':
    VoiceApp().run()