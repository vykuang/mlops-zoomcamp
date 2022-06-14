import pickle

import logging

from flask import Flask, request, jsonify

# Read from model registry instead of local dir
# with open('lin_reg.bin', 'rb') as f_in:
#     (dv, model) = pickle.load(f_in)

def prepare_features(ride):
    features = {}
    features['PU_DO'] = f"{ride['PULocationID']}_{ride['DOLocationID']}"
    features['trip_distance'] = ride['trip_distance']
    return features

def predict(features):
    X = dv.transform(features)
    preds = model.predict(X)
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
    logging.info('Received POST request')

    features = prepare_features(ride)
    preds = predict(features)
    result = {
        'duration': preds
    }

    logging.info('Duration prediction made')

    # jsonify improves upon json.dumps
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, 
            host='0.0.0.0', # expose port on all interfaces
            port=9696
    )