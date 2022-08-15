import os
import json
# import argparse
import logging
# import string
# allows os.getenv to use env vars defined in .env,
# without them actually being exported in the environment
from dotenv import load_dotenv

from flask import Flask, request, jsonify

import mlflow
# from mlflow.tracking import MlflowClient

# pub client to send to a push topic that triggers a cloud function
# as well as a sub client to receive func output from the pull topic
from google.cloud import pubsub_v1

# MLFLOW_TRACKING_URI = 'http://13.215.46.159:5000/'
# how do I parametrize this when running from CLI?
# include in a local .env for docker to COPY from?
# use --env-file=.env in docker run
# TRACKING_IP = '13.215.46.159'
# EXP_NAME = 'green-taxi-duration'
# RUN_ID = '815e49bd6e69425d977f2042f7f74c97'

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# load env var from .env file as if it was actually EXPORTed
# TRACKING_IP = os.getenv('TRACKING_IP')
# EXP_NAME = os.getenv('EXP_NAME')

# only RUN_ID necessary if we're pulling directly from S3
RUN_ID = os.getenv('RUN_ID')

# pub/sub info
PROJECT_ID = os.getenv('PROJECT_ID')
PUBLISHER_TOPIC_NAME = os.getenv('BACKEND_PUSH_STREAM')
SUBSCRIBER_ID = os.getenv('BACKEND_PULL_SUBSCRIBER_ID')

publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

publisher_path = publisher.topic_path(PROJECT_ID, PUBLISHER_TOPIC_NAME)
subscriber_path = subscriber.topic_path(PROJECT_ID, SUBSCRIBER_ID)

def prepare_features(ride):
    print('prepping features')
    features = {}
    features['PU_DO'] = f"{ride['PULocationID']}_{ride['DOLocationID']}"
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


def send_to_stream(message_json):
    message_bytes = message_json.encode("utf-8")

    try:
        publish_future = publisher.publish(publisher_path, data=message_bytes)
        publish_future.result()

        return "Message published."
    except Exception as e:
        print(e)
        return (e, 500)

def receive():

    response = subscriber.pull(
        request={
            'subscription': subscriber_path,
            'max_messages': 1,
        }
    )

    msg = response.received_messages[0]
    ack_id = msg.ack_id
    subscriber.acknowledge(
        request={
            'subscripiton': subscriber_path,
            'ack_ids': [ack_id],
        }
    )
    
    data = json.loads(msg.message.data)
    return data

# name of our flask app
app = Flask('duration-prediction')

# name our route something different than our app
# i.e. what actions it's doing
@app.route('/predict', methods=['POST'])
def predict_endpoint():
    """Joining the above funcs into one invocation triggered
    by an HTTP POST request
    POST because client needs to provide the required features
    for web service to make the prediction
    """
    # from the POST request
    ride = request.get_json()
    print('received POST')
    logging.info('Received POST request')

    features = prepare_features(ride)
    preds = predict(features)
    result = {
        'duration': preds,
        'model_version': RUN_ID,
    }

    logging.info('Duration prediction made')

    # jsonify improves upon json.dumps
    return jsonify(result)

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=9696,
    )