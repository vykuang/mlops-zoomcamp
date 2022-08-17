"""
Test function to pull messages from pub/sub topic
"""

import os
import json
from google.cloud import pubsub_v1
from dotenv  import load_dotenv
from pathlib import Path

dotenv_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=dotenv_path)


PROJECT_ID = os.getenv("PROJECT_ID")
SUB_ID = os.getenv('BACKEND_PULL_SUBSCRIBER_ID')

subscriber = pubsub_v1.SubscriberClient()

subscriber_path = subscriber.subscription_path(PROJECT_ID, SUB_ID)

def receive():
    response = subscriber.pull(
        request={
            'subscription': subscriber_path,
            'max_messages': 1,
        }
    )

    # acknowledge reception
    msg = response.received_messages[0]
    ack_id = msg.ack_id
    subscriber.acknowledge(
        request={
            'subscription': subscriber_path,
            'ack_ids': [ack_id],
        }
    )
    data = json.loads(msg.message.data)
    return data

if __name__ == '__main__':
    print(receive())