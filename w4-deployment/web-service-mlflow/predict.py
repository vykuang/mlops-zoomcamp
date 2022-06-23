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
EXP_NAME = 'nyc-taxi-experiment'
RUN_ID = '8fa4fdbc841b4a0e9a2670080dbeabd4'

# Read from model registry instead of local dir
# with open('lin_reg.bin', 'rb') as f_in:
#     (dv, model) = pickle.load(f_in)

def prepare_features(ride):
    features = {}
    features['PU_DO'] = f"{ride['PULocationID']}_{ride['DOLocationID']}"
    features['trip_distance'] = ride['trip_distance']
    return features

def predict(features, dv, name, stage):
    X = dv.transform(features)
    model_uri = f'models:/{RUN_ID}/model'
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    preds = model.predict(X)
    # casts from numpy to regular python type
    # to allow serialization
    return float(preds[0])

def fetch_dv(client, run_id):
    dst_path = './models/'
    client.download_artifacts(
        run_id=run_id, 
        path='dict_vectorizer.bin',
        dst_path=dst_path
    )
    logging.info(f'downloading dict vectorizer to {dst_path}')
    with open('models/dict_vectorizer.bin', 'rb') as f_in:
        dv = pickle.load(f_in)
    return dv

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
    logging.info('Received POST request')


    
    tracking_uri = f'http://{TRACKING_IP}/5000'
    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(EXP_NAME)

    dv = fetch_dv(client, run_id)
    features = prepare_features(ride)
    preds = predict(features)
    result = {
        'duration': preds
    }

    logging.info('Duration prediction made')

    # jsonify improves upon json.dumps
    return jsonify(result)

if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     '--host', '-h',
    #     default='0.0.0.0',
    #     help='IP to host the prediction app; defaults to 0.0.0.0',
    # )
    # parser.add_argument(
    #     '--port', '-p',
    #     default=9696,
    #     type=int,
    #     help='Port exposed for prediction app; defaults to 9696',
    # )
    # parser.add_argument(
    #     '--mlflow_ip', '-m',
    #     type=string,
    #     default='13.215.46.159',
    #     help='IP address of MLflow tracking server from which to pull the model',
    # )
    # args = parser.parse_args()
    # app.run(args.host, # expose port on all interfaces
    #         args.port,
    #         args.mlflow_ip,
    #         debug=True, 
    app.run(
        debug=True,
        host='0.0.0.0',
        port=9696,
    )