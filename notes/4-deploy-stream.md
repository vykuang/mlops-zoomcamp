# Deploying Streaming Pipeline in GCP

[Notes taken from here](https://gist.github.com/Qfl3x/de2a9b98a370749a4b17a4c94ef46185), which are based off this lecture from [mlops-zoomcamp](https://www.youtube.com/watch?v=TCqr9HNcrsI&list=PL3MmuxUbc_hIUISrluw_A7wDSmfOhErJK&index=35)

Original tutorial used AWS but kinesis did not have a free tier usage and so I'm switching to GCP

Core components of our example workflow:

1. Backend to receive trip context from user
2. Backend may provide a coarse estimation of ride duration
3. Once user confirms ride, backend may request a more accurate duration prediction via a stream pipeline
4. The streaming pipeline returns the more accurate figure to backend through the event stream
 
## Setup GCP pub/sub

### Outline

1. Create data stream (Push Topic, called `BACKEND_PUSH_STREAM`) to publish data (json format) from backend (publisher) to consumer func (subscriber). 
2. Create the consumer function to collect inputs from push stream topic
3. Deploy consumer function as google function (or AWS lambda???)
4. Create Topic B (Pull Topic, called `BACKEND_PULL_STREAM`) to ingest output from the function
5. Pull prediction output from topic B to backend

In additition these directories will be needed:

1. backend with a simple predictor
2. consumer function

### Backend

Backend in this case refers to dockerized flask setup that returns a ride duration prediction when `POST`ed with ride parameter json


### IAM service account

- Service account - name it `function-pubsub-role`
- Roles:
  - pub/sub service agent
  - functions service agent
- Add key and save the json for our terminal to use
  - The key directory will be referenced by env var `GOOGLE_APPLICATION_CREDENTIALS`

### Consumer function directory

Directory must contain `main.py`. If it has any other dependencies, i.e. the model to be loaded, they should also be present. 

Alternatively, the function can retrieve the models either from cloud storage or from wherever the MLflow artifact bucket is located, e.g. AWS S3

### Create push stream topic

1. Set env var `PUSH_TOPIC`
2. `gcloud pubsub topics create $PUSH_TOPIC

Alternatively, use a script func to create the topic:

```python
from google.cloud import pubsub_v1

#1. Initialize Client
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("BACKEND_PUSH_STREAM")

topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
```

To use the push topic to send messages, we have a send() func:

```python

def send(message_json):
        #2. Encode the message json
        message_bytes = message_json.encode('utf-8')
        
        try:
            #3. Publish the message to the topic
            publish_future = publisher.publish(topic_path, data=message_bytes)
            #4. Verify that the message has arrived
            publish_future.result()  # Verify the publish succeeded

            return 'Message published.'
        except Exception as e:
            print(e)
            return (e,500)

ride = {'datetime':'2022-06-23 11:36:42',
        'PULocationID': 34,
        'DOLocationID': 56,
        'trip_distance': 12
        }
ride = json.dumps(ride)
send(ride)
```

After initializing the publisher client:

2. encode our message in json
3. publish the encoded msg to topic client
4. Confirm msg publishing

The terminal running this script must have necessary permission to publish message to pubsub

### Consumer function

The actual function to be run, placed inside `main.py`, will need to handle two inputs: `event`, and `context`:

```python
def predict_duration(event, context):
    ride = base64.b64decode(event['data']).decode('utf-8')
    ride = json.loads(ride)

    D = preprocess_dict(ride)
    X = vectorize(ride)
    predicted_duration = round(predict(X))
    return_dict = {'duration_final': predicted_duration}
    print(return_dict) #For Debugging
```

Like AWS kinesis, `event` is the received message containing the data, encoded in base64. `context` is meta info about the event. Our consumer func will be mainly concerned with `event`. Since it is encoded, it must be *decoded* to retrieve the json. 

Then like normal will be pre-processed and fed to our predictor model.

### Deploying consumer func

To deploy the `predict_duration()` func that' resides in `main.py`, we invoke `gcloud functions` in CLI:
