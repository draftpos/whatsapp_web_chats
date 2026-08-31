import requests
import json
import time

def send_test_message():
    print("Connecting Wasphere to Odoo...")
    url = "http://localhost:8069/api/flutter/receive_message"
    
    # Odoo type='json' routes require JSON-RPC format
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "account_id": 1,
            "sender_phone": "263777123456",
            "sender_name": "Test User From WhatsApp",
            "body": "Hello! This is a real-time test message from Wasphere to Odoo!",
            "message_id": f"MSG_{int(time.time())}"
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Response Code:", response.status_code)
        print("Response Body:", response.text)
        print("\nSuccess! Check your Odoo screen, the message should have popped up!")
    except Exception as e:
        print("Error connecting to Odoo:", e)

if __name__ == "__main__":
    send_test_message()
