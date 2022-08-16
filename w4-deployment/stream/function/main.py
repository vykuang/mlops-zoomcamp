import os
from pathlib import Path
import json
import base64
from dotenv import load_dotenv

import mlflow
from google.cloud import pubsub_v1

# relies on env vars being set

dotenv_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path)

# GCP 
PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("BACKEND_PULL_STREAM")
# MODEL_BUCKET = os.getenv("MODEL_BUCKET")

# MLflow
RUN_ID = os.getenv('RUN_ID')


def prepare_features(ride):
    features = {}
    features['PU_DO'] = '%s_%s' % (ride['PULocationID'], ride['DOLocationID'])
    features['trip_distance'] = ride['trip_distance']
    return features


def predict(features):
    '''
    Model is now a sklearn pipeline object which combines the dict_vect
    as well as the random forest model
    '''

    # full s3 path: s3://bucket_name/<exp_id>/run_id/artifacts/model
    model_uri = f's3://mlflow-artifacts-remote-1212/3/{RUN_ID}/artifacts/model/'
    print('loading model')
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    preds = model.predict(features)
    # casts from numpy to regular python type
    # to allow serialization
    return float(preds[0])


publisher = pubsub_v1.PublisherClient()

def send(message_json):
    """
    Sends message to the Pull stream"""
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

    message_bytes = message_json.encode("utf-8")
    print(message_bytes)
    # pylint: disable=W0703, C0103
    try:
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()  # Verify the publish succeeded

        return "Message published."
    except Exception as e:
        print(e)
        return (e, 500)

def predict_duration(event, context):
    """
    Main function to be exported.
    Takes the event and outputs the prediction and sends it to the Pull stream"""

    # pred_events = []

    # for record in event['Records']:
    decoded_ride = base64.b64decode(event["data"]).decode("utf-8")
    ride_event = json.loads(decoded_ride)

    # the message I'm sending from publish.py is just sending the ride dict
    # ride = ride_event['ride']
    # ride_id = ride_event['ride_id']

    features = prepare_features(ride_event)
    pred = predict(features)

    return_dict = {"duration_final": pred}
    print(f"duration_final: {pred}")
    # print(f"reinitiated: {reinitiated}")
    send(json.dumps(return_dict))