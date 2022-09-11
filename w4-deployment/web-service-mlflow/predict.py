import logging
import os

import mlflow
from flask import Flask, jsonify, request
from mlflow.tracking import MlflowClient

# MLFLOW_TRACKING_URI = 'http://${MLFLOW_IP}:5000/'
# how do I parametrize this when running from CLI?
# export to shell env var before runniing this as script
# if dockerized, env vars will be passed in .env file
MLFLOW_TRACKING_IP = os.getenv("MLFLOW_TRACKING_IP")
MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME")
MLFLOW_RUN_ID = os.getenv("MLFLOW_RUN_ID")
MLFLOW_MODEL_URI = os.getenv("MLFLOW_MODEL_URI")


def prepare_features(ride):
    print("prepping features")
    features = {}
    features["PU_DO"] = f"{ride['PULocationID']}_{ride['DOLocationID']}"
    features["trip_distance"] = ride["trip_distance"]
    return features


def predict(features):
    """
    Model is now a sklearn pipeline object which combines the dict_vect
    as well as the random forest model
    """

    # full s3 path: s3://bucket_name/<exp_id>/run_id/artifacts/model
    model_uri = MLFLOW_MODEL_URI
    print("loading model")
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    preds = model.predict(features)
    # casts from numpy to regular python type
    # to allow serialization
    return float(preds[0])


def save_to_db():
    """Save prediction metadata to a DB for batch monitoring"""
    pass


def send_to_evidently():
    """Send online prediction metadata to Evidently for realtime monitoring"""
    pass


# name of our flask app
app = Flask("duration-prediction")

# name our route something different than our app
# i.e. what actions it's doing
@app.route("/predict", methods=["POST"])
def predict_endpoint():
    """Joining the above funcs into one invocation triggered
    by an HTTP POST request
    POST because client needs to provide the required features
    for web service to make the prediction
    """
    # from the POST request
    ride = request.get_json()
    logging.info("Received POST request")

    features = prepare_features(ride)
    preds = predict(features)
    result = {
        "duration": preds,
        "model_version": MLFLOW_RUN_ID,
    }
    logging.info("Duration prediction made")

    save_to_db()
    send_to_evidently()

    # jsonify improves upon json.dumps
    return jsonify(result)


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=9696,
    )
