# Model Deployment

## Batch vs Online

Determine the requirement of the end-user. Can they afford to wait for results, or is realtime required?

### Batch

Model could regularly pull data from DB, run model, evaluate

* Customer churn could be on a monthly basis
* Ride duration may be require half-hour update basis, so customers have a semi-up to date information on whether they should bother.

Usually 1 to 1 client-server relationship

### Web service

Flask and Docker

### Streaming

Typically 1-to-many relation between pipeline and data consumer

Once a ride has started, data could be streamed to multiple services:

1. Tip prediction
2. ride duration (more accurate version using more finely grained data)

Another example with video streaming, in particular content moderation. User uploading a video is an event in a streaming pipeline that could trigger the following services:

1. copyright violation
2. NSFW
3. violence

Decisions from each of those services could stream to another pipeline, consumed by a centralized decision service.

Services could be added above that also feeds into the centralized decision service, to provide another point of data on whether the video should be removed or not.

## Web services - Deployment with Flask and Docker

To build our docker image, use `pipenv` to get the requirements list and create the venv. Can be used inside `conda` environment if we specify the python to be the one used by the conda env.

Or more simply just specify which python version we want, and it'll grab the bin and store it in the .virtualenv directory:

```bash
cd ~/<project_dir>
pipenv install scikit-learn==1.0.2 flask --python=3.9
# venv and pipfile is created

# activates venv
pipenv shell

# view installed dependencies
deploy$ pipenv graph
Flask==2.1.2
  - click [required: >=8.0, installed: 8.1.3]
  - importlib-metadata [required: >=3.6.0, installed: 4.11.4]
    - zipp [required: >=0.5, installed: 3.8.0]
  - itsdangerous [required: >=2.0, installed: 2.1.2]
  - Jinja2 [required: >=3.0, installed: 3.1.2]
    - MarkupSafe [required: >=2.0, installed: 2.1.1]
  - Werkzeug [required: >=2.0, installed: 2.1.2]
scikit-learn==1.0.2
  - joblib [required: >=0.11, installed: 1.1.0]
  - numpy [required: >=1.14.6, installed: 1.22.4]
  - scipy [required: >=1.1.0, installed: 1.8.1]
    - numpy [required: >=1.17.3,<1.25.0, installed: 1.22.4]
  - threadpoolctl [required: >=2.0.0, installed: 3.1.0]

# where's our venv?
deploy$ which python
/home/kohada/.local/share/virtualenvs/w4-deployment-xcyXzTh1/bin/python
```

Great. Don't think we'll actually get to use this venv; we just need the pipfile and pipfile.lock to import into our docker image for production I think.

### Isolating environment with docker

So far our app needs 

* flask for the web app, and 
* sklearn for the actual prediction

But also, requests for testing, so we'll install as a dev package by `pipenv install --dev requests`. This way, requests won't be in the production env. Our Pipfile now looks like:

```Pipfile
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
scikit-learn = "==1.0.2"
flask = "*"
gunicorn = "*"

[dev-packages]
requests = "*"

[requires]
python_version = "3.9"
```

To get that venv onto a container and run our `predict.py` app, run this Dockerfile

```docker
FROM python:3.9-slim

# gets the latest pip
RUN pip install --upgrade pip

# to use our Pipfile and Pipfile.lock
RUN pip install pipenv

# './' below is relative to our WORKDIR
WORKDIR /app

# need to use double quotes
# For > 2 args, all args are considered files except
# for the last, which will be the destination folder
COPY [ "Pipfile", "Pipfile.lock", "./"]

# no need to create a venv inside a docker container 
# for this case
# deploy enforces that pipfile.lock is up-to-date
# otherwise it fails the build, instead of generating a new one
RUN pipenv install --system --deploy

COPY [ "predict.py", "lin_reg.bin", "./" ]

EXPOSE 9696

ENTRYPOINT [ "gunicorn", "--bind", "0.0.0.0:9696", "predict:app"]
```

Build with `docker build -t duration-prediction-webapp:v1 .`; don't forget the `.` to denote that the Dockerfile is in current directory.

Run with `docker run -it --rm -p 9696:9696 duration-prediction-webapp:v1`

Test with the same `python test_predict.py` and it should return the same JSON.

## Web services with MLflow

Our previous container copied the model directly from directory. Now let's integrate with MLflow so we can grab `production` grade trained model from the MLflow registry.

### Set up the MLflow components on AWS

#### Create IAM role with access to S3 and RDS

IAM > Users > create (name as mlflow-admin) > select policies:

1. S3 FULL ACCESS
2. RDS FULL ACCESS

I created a group with those two policies.

In the EC2 instance (assuming AMI image, otherwise need `sudo yum install awscli`), enter the role's auth info with `aws configure`

#### registry on S3 bucket

Before we can pull the model from registry, let's build the registry first. We'll use the notebook from week 2, but this time we'll set the artifact store to our cloud bucket.

* name - `mlflow-artifact-remote-1212`
* region - `ap-southeast1`

Confirm access with `aws s3 ls` to list buckets and 

#### backend on RDS (postgres)

RDS > create database > postgresql > FREE TIER!!!

Once 

[Doc on connecting](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_CommonTasks.Connect.html)

#### Setup tracking server on EC2

On the clean instance, run

```bash
sudo yum update
pip3 install mlflow boto3 psycopg2-binary
# enter the role access key ID/secret access for the role
# with the necessary permissions (re: S3 and RDS)
aws configure 
# start instance, if env vars are set
mlflow server -h 0.0.0.0 -p 5000 --backend-store-uri postgresql://${MLFLOW_DB_USER}:${MLFLOW_DB_PASSWORD}@${MLFLOW_DB_ENDPOINT}:5432/${MLFLOW_DB_NAME} --default-artifact-root s3://${MLFLOW_BUCKET}

## plain text version
mlflow server -h 0.0.0.0 -p 5000 \
  --backend-store-uri postgresql://mlflow:32etqvogXjb7dcbX1su9@mlflow-backend-remote.cspfunjl7cni.ap-southeast-1.rds.amazonaws.com:5432/mlflow_db \
  --default-artifact-root s3://mlflow-artifacts-remote-1212
```

Maybe put the auth stuff in `.env` and `source .env` to use them as shell variables.

When running `train.py` to access the remote tracking server, ran into this error: `WARNING mlflow.utils.autologging_utils: Encountered unexpected error during sklearn autologging: Unable to locate credentials`. 

Resolution: Include AWS credentials to localhost machine. Even though the remote tracking server already has that info, the localhost also needs to contact the remote artifact store (S3) per this schematic:

![mlflow scenario 4](./img/scenario_4.png)

Two ways to store AWS credential to access S3 artifact store [per aws documentation](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/setup.html#setup-credentials):

1. store in `~/.aws/credentials` 
2. `export AWS_ACCESS_KEY_ID=key_id_here AWS_SECRET_ACCESS_KEY=secret_here`
3. env vars are prioritized before `credentials` file
   * `unset` can clear environment vars
   * Notebook inside vs code curiously held my previous access key, even though the credentials file had the correct pair. Even when I used `echo $AWS_SECRET_ACCESS_KEY` within the VS terminal, the correct one came out. Even after installing awscli, the notebook still retained the previous one. Use unset.
   * Still giving `S3UploadFailedError`
   * Add `region = ca-central-1` in credentials
   * NO dice
   * The jupyter environment inside VS is somehow not recognize any of the env variables, even after setting `os.environ['KEY'] = value`. Works when I migrated the code to `rf.py`

Alternatively, we can avoid having end-user (me) needing to manage artifact via scenario 5: MLflow Tracking Server enabled with proxied artifact storage access. This must be set when starting the server with `mlflow server --backend-store-uri postgresql://URI --artifacts-destination s3://bucket_name/mlartifacts --serve-artifacts --host ...` 

Going further along this vein, if we only need the tracking server to serve artifacts, and not log any additional training (i.e. for deployment purposes), we can start the MLflow server via `--artifacts-only` flag which disables all Tracking Server functionality. Again this decouples the user from credential management. [Scenario 6 in MLflow docs](https://www.mlflow.org/docs/latest/tracking.html#id33)

Access with `http://13.215.46.159:5000/`

#### Register top model

### Retrieve model from MLflow registry instead

Run `rf.py` to log the pipeline (dict vect + random forest model) onto the S3 bucket for our predict app to retrieve

Use the full S3 path given on the artifacts page.

The container must also have the aws credential in order to access the S3 path. Couple options:

1. Mount the ~/.aws/ directory as a volume: `docker ... -v /home/user/.aws:/root/.aws`
2. Pass as .env inside Dockerfile

## Streaming: Deployment with Kinesis and Lambda

Kinesis is AWS' answer to streaming data processing; similar to Apache kafka, they are both **data ingest frameworks** prioritizing durability, reliability, and scalability. GCP's equivalent is *Pub/Sub*.

Key differences

1. Kafka is open-source, first developed at LinkedIn. Kinesis is managed.
   * Users are responsible for installing and managing clusters
   * Managed means that users pay for a fully set up cluster. Less overhead
2. Cost can vary wildly due to the fact that Kafka needs to be set up, and thus requires DevOps and resource costs (e.g. EC2 instances to run Kafka). Even though there's a greater upfront fee associated with Kinesis it may be more cost effective due to minimal DevOps/resource being used to maintain it
3. Kinesis auto-scales capacity.
4. Some API differences re: last message

[Official tutorial from AWS on kinesis and lambda](https://docs.amazonaws.cn/en_us/lambda/latest/dg/with-kinesis-example.html)

[Tutorial for just lambda](https://docs.amazonaws.cn/en_us/lambda/latest/dg/getting-started.html#getting-started-create-function)

Lambda is equiv to GCP's cloud functions - run code without servers

### Context

In context of our ride duration prediction, perhaps we use an older, batch-trained model for the initial estimate, and we stream real time predictions using a more advanced model but more selectively to conserve resources.

### Create Role in IAM

To run the lambda code, it needs a role attached to it, with proper permissions to access AWS resources.

* Create *Role*
* Select *lambda* as use case, and search for *[AWSLambdaKinesisExecutionRole](https://us-east-1.console.aws.amazon.com/iam/home#/policies/arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole)*
  * Contains a set of permissions for our lambda (serverless code) to read kinesis streams
  * and log to CloudWatch
* name it `lambda-kinesis-role`

### Create lambda function

The lambda template:

```python
import json

def lambda_handler(event, context):
    # TODO implement
    print(json.dumps(event))
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
```

* `event` is the trigger
  * contains the `json` data sent to the lambda function
  * Test with a sample json with `json.dumps(event)`:
  * ```json
    {
      "key1": "value1",
      "key2": "value2",
      "key3": "value3"
    }
    ```
  * In order to test updated code, click DEPLOY; will not use new code otherwise
