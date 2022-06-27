import pickle
# import argparse
import logging
# import string

from flask import Flask, request, jsonify

import mlflow
from mlflow.tracking import MlflowClient

# MLFLOW_TRACKING_URI = 'http://13.215.46.159:5000/'
# how do I parametrize this when running from CLI?
TRACKING_IP = '13.215.46.159'
EXP_NAME = 'green-taxi-duration'
RUN_ID = '815e49bd6e69425d977f2042f7f74c97'


def prepare_features(ride):
    print('prpepping features')
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