import requests
import hashlib
import random
import string
import time
import csv
import os
from langchain_core.tools import tool

APP_ID = '1496457656775585792f04a4'
APP_KEY = '653y3nrp01al2nt6fmor6skkhbbl3bmg'
KEY_ID = 'K.1496457656834306048'
BASE_URL = 'https://open-sg.aqara.com/v3.0/open/api'
ACCESS_TOKEN = '5e7077856efad4eaac5dbae8e155390d'
DID = 'lumi1.54ef449c5dd2'
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'files', 'fp2-log.csv')

def get_headers():
    nonce = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    timestamp = str(int(time.time() * 1000))
    sign_str = f'Accesstoken={ACCESS_TOKEN}&Appid={APP_ID}&Keyid={KEY_ID}&Nonce={nonce}&Time={timestamp}{APP_KEY}'
    sign = hashlib.md5(sign_str.lower().encode()).hexdigest()
    return {
        'Content-Type': 'application/json',
        'Appid': APP_ID,
        'Keyid': KEY_ID,
        'Nonce': nonce,
        'Time': timestamp,
        'Sign': sign,
        'Accesstoken': ACCESS_TOKEN,
        'Lang': 'en'
    }

def api_call(intent, data):
    response = requests.post(
        BASE_URL,
        json={'intent': intent, 'data': data},
        headers=get_headers()
    )
    return response.json()

@tool
def get_fp2_presence(query: str) -> str:
    """Query the Aqara FP2 presence sensor for current occupancy and light level.
    Use this when asked about room presence, occupancy, whether someone is in the room,
    or current light/illuminance levels."""
    try:
        result = api_call('query.resource.value', {
            'resources': [{
                'subjectId': DID,
                'resourceIds': ['3.51.85', '0.4.85']
            }]
        })
        if result.get('code') != 0:
            return f"Error querying FP2: {result.get('message')}"

        data = {}
        for item in result.get('result', []):
            data[item['resourceId']] = item['value']

        presence = data.get('3.51.85', '0')
        illuminance = data.get('0.4.85', 'unknown')
        occupied = presence == '1'

        return (
            f"FP2 Presence Sensor Status:\n"
            f"- Occupancy: {'Someone is present' if occupied else 'No one detected'}\n"
            f"- Light level: {illuminance} lux\n"
            f"- Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_fp2_history(query: str) -> str:
    """Query the FP2 presence sensor log history.
    Use this when asked about past presence data, history, or trends."""
    try:
        if not os.path.exists(LOG_FILE):
            return "No log file found. Make sure the Node.js server is running and logging data."

        rows = []
        with open(LOG_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        if not rows:
            return "Log file is empty."

        last = rows[-10:]
        summary = f"Last {len(last)} log entries from FP2:\n"
        for row in last:
            occupied = row.get('occupied', 'false') == 'true'
            summary += (
                f"- {row.get('datetime', 'unknown')}: "
                f"{'Occupied' if occupied else 'Empty'}, "
                f"Light: {row.get('illuminance', '?')} lux\n"
            )
        return summary
    except Exception as e:
        return f"Error reading log: {str(e)}"
