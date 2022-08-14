from google.cloud import pubsub_v1, storage

# relies on env vars being set
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("BACKEND_PULL_STREAM")
MODEL_BUCKET = os.getenv("MODEL_BUCKET")

def predict_duration(event, context):
    """
    Main function to be exported.
    Takes the event and outputs the prediction and sends it to the Pull stream"""

    ride = base64.b64decode(event["data"]).decode("utf-8")
    ride = json.loads(ride)

    preprocessed_dict = preprocess_dict(ride)
    model_features = vectorize(preprocessed_dict)
    predicted_duration = round(predict(model_features))
    return_dict = {"duration_final": predicted_duration}
    print(f"duration_final: {predicted_duration}")
    # print(f"reinitiated: {reinitiated}")
    send(json.dumps(return_dict))