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

Create a pipenv in the main `stream` project folder with:

1. google-cloud-pubsub
2. scikit-learn~=1.0.2
3. mlflow
4. boto3 (to access aws s3)
5. python-dotenv (to load_dotenv)

### Backend

Backend in this case refers to dockerized flask setup that returns a ride duration prediction when `POST`ed with ride parameter json

When running the container, since we're sending and pulling messages to and from pub/sub, we need to include the service account key json, and export the `GOOGLE_APPLICATION_CREDENTIALS' env var to point to it. Otherwise it will not have permission to access those resources

### IAM service account

- Service account - name it `function-pubsub-role`
- Roles:
  - pub/sub service agent
  - functions service agent
- Add key and save the json for our terminal to use
  - The key directory will be referenced by env var `GOOGLE_APPLICATION_CREDENTIALS`
  - In .bashrc and .profile, add `export G_A_C=${HOME}/.gcp/service-account-key.json`, for example

### Consumer function directory

Directory must contain `main.py`. If it has any other dependencies, i.e. the model to be loaded, they should also be present. 

Alternatively, the function can retrieve the models either from cloud storage or from wherever the MLflow artifact bucket is located, e.g. AWS S3

### Create push stream topic

1. Set env var `PUSH_TOPIC`
2. `gcloud pubsub topics create $PUSH_TOPIC
3. Named `ride-data-push`

Alternatively, use a script func to create the topic:

```python
from google.cloud import pubsub_v1

#1. Initialize Client
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("TOPIC_NAME")

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

2. encode our message in json. Note that it needs to be a json already, hence `ride = json.dumps(ride)` in the line before send().
3. publish the encoded msg to topic client
4. Confirm msg publishing

The terminal running this script must have necessary permission to publish message to pubsub

### Consumer function

The actual function to be run, placed inside `main.py`, will need to handle two inputs: `event`, and `context`:

```python
import base64
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

```bash
gcloud functions deploy predict_duration \
	--trigger-topic $BACKEND_PUSH_STREAM \
	--runtime=python39 \
	--set-env-vars FOO=bar,FAA=baz
```

* `predict_duration` is the func to run inside `main.py`
* messages received in the `$BACKEND_PUSH_STREAM` topic (sent by our backend) will trigger this func
* alternatively use `--env-vars-file=".env.yaml"` to write them out beforehand: `VAR: VALUE`. 
* I decided to put the creds inside the .yaml and removed it from version control
* `deploy` does have `--set-secrets` argument, so something to look into.
* Okay so it turns out, all of it's uploaded to the functions workspace in the cloud if it's not in .gcloudignore. Excellent.


#### Cloud Function Dependencies

Dependencies of `main.py` are defined in a `requirements.txt`:

```
python-dotenv
mlflow
scikit-learn==1.0.2
google-cloud-pubsub
```

#### .gcloudignore

This is an optional config file to specify which of the files in our `function` dir should not be uploaded. We could use it to specify `publish.py` that tested our pub/sub topic.

#### Deployment

Saved the above bash cmd to `deploy.sh` and ran it; asked to enable `Cloud Build`, presumably to make use of the `requirements.txt` and build the dependencies required for our function.

Test it by running `publish.py`

Misread the incoming `ride` json. Redeploy the source by adding `--source=.` in `deploy.sh`. Takes a long time...

Okay. MLflow needs `boto3`, and I need to remove the access keys.

Use google secrets manager. Apparently there is a free tier. Six active keys/month. Yay! Created via Console. Too late to figure out CLI but it looks something like `gcloud secrets create "my-secret-id" --replication-policy="automatic" --data=SECRET_VALUE.

Then, when I deploy the func, I add the flag `--set-secrets "MY_SECRET=my-secret-id:latest":

* `my-secret-id` is what I named the secret in manager; in doc it's called `SECRET_VALUE_REF`
* `MY_SECRET` is how the function will use this environment variable secret.
* `:latest` refers to the different versions of the secret, i.e. if there's a rotating key? Or if I just have a new secret key, I can keep the name and the meta-info but use a new key.

Deploy then looks like:

```bash
#!/usr/bin/env bash
gcloud functions deploy predict_duration \
    --trigger-topic $BACKEND_PUSH_STREAM \
    --env-vars-file=".env.yaml" \
    --runtime=python39 \
    --set-secrets='AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID:latest,' \
    --set-secrets='AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY:latest'
```

Terminal gave this warning:

```
WARNING: This deployment uses secrets. Ensure that the runtime service account 'mlops-zoom-351813@appspot.gserviceaccount.com' has access to the secrets. You can do that by granting the permission 'roles/secretmanager.secretAccessor' to the runtime service account on the project or secrets.
E.g. gcloud projects add-iam-policy-binding mlops-zoom-351813 --member='serviceAccount:mlops-zoom-351813@appspot.gserviceaccount.com' --role='roles/secretmanager.secretAccessor'
```

Service account needs access to secrets.

My appspot gservice account did not have such access. Do I need to supply google credentials as well?

Unless otherwise specified, function will use a **default service account**:

* gen1 uses App Engine default
* gen2 uses default compute service

These defaults have **Editor** role, allowing broad access, *but not secret accessor*.

Even after deployment, the functioni's runtime service account can be modified: EDIT > Runtime settings > Runtime service account > function-pubsub-role. I've added the secret accessor permission to the pubsub role. This page also shows in plaintext the runtime env variables.

Mem lim exceeded after calling S3 model. Try 512 mb

Ok. New error message: Failed to publish, permission denied. So we've made the prediction, and the func is now trying to publish to the pull stream and somehow I don't have that permission???

Replaced `Cloud pub/sub service agent` with `Pub/Sub Editor` to allow `pubsub.topics.publish`. IT WORKEDDDD

### Pulling data from `ride-duration-pull` stream

```python
PROJECT_ID = os.getenv("PROJECT_ID")
SUB_ID = os.getenv('BACKEND_PULL_SUBSCRIBER_ID')

# 1. Initialize client
subscriber = pubsub_v1.SubscriberClient()

subscriber_path = subscriber.subscription_path(PROJECT_ID, SUB_ID)

def receive():
    # 2. Pull request, specifying the path via project_ID and sub_ID
    response = subscriber.pull(
        request={
            'subscription': subscriber_path,
            'max_messages': 1,
        }
    )

    # 3. acknowledge reception
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
```

## Deploying in docker

### GCP credentials

If we're launching docker from GCP compute, perhaps we do not need to set $GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/secret.json. Yuuup.
However if we're launching docker locally, [follow this doc to authenticate with GCP](https://cloud.google.com/run/docs/testing/local#docker-with-gcp-access). Boils down to setting the env var, and bind-mounting the secret.json to tmp/keys/secret.json
### Docker

1. Cannot load model from S3.

Remove single quotes around RUN_ID in my .env. Also my .env needs to be duplicated to be in same directory as the Dockerfile. Anyway, the single quotes were taken literally when substituted into the URI and caused "resource not found" issue.

Same problem for GCP env vars.

2. dict has no encode. My send_to_stream() func takes in a json, so use `json.dumps(ride)` 
3. Updating code in Docker. A couple approaches:
	1. Load the script in a mount so it updates as we edit. Good for local dev
	2. Leave the `COPY [ "script.py", "./" ]` line last. Take advantage of how Docker caches each layer, so that we don't have to re-run pipenv install every time we re-build the image. General rule of thumb: leave the most frequently changed line LAST in Dockerfile so that it can just rebuild on the second last layer.
4. When I test too frequently, it pulls the incorrect message from the pull topic. I think one way to confirm is to keep the datetime and make sure the result datetime matches the POSTed datetime. If datetime may be duplicated, may need to generate IDs? or perhaps combine datetime with some other keys to ensure uniqueness.
