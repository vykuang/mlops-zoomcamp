"""
Demo of loading our .env and sending a message to a push topic
"""
import os
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import pubsub_v1

#1. Initialize Client
publisher = pubsub_v1.PublisherClient()

# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path)

PROJECT_ID = os.getenv("PROJECT_ID")
PUBLISHER_TOPIC_NAME = os.getenv("BACKEND_PUSH_STREAM")

topic_path = publisher.topic_path(PROJECT_ID, PUBLISHER_TOPIC_NAME)

def send_to_stream(message_json):
    message_bytes = message_json.encode("utf-8")

    try:
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()

        return "Message published."
    except Exception as e:
        print(e)
        return (e, 500)

if __name__ == '__main__':
    ride = {
        'datetime':f'{datetime.now()}',
        'PULocationID': 34,
        'DOLocationID': 56,
        'trip_distance': 55
    }
    
    send_to_stream(json.dumps(ride))
