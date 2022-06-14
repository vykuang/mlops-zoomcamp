import requests

# sample data
ride = {
    "PULocationID": 10,
    "DOLocationID": 50,
    "trip_distance": 40
}

# testing locally without web service
# features = predict.prepare_features(ride)
# pred = predict.predict(features)
# print(pred[0])

# testing against the flask service
url = 'http://localhost:9696/predict'
response = requests.post(url, json=ride)
print(response.json())