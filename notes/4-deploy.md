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

Run with `docker run -it --rm -p 9696:9696 duration-prediction-we
bapp:v1`

Test with the same `python test_predict.py` and it should return the same JSON.

## Web services with MLflow

Our previous container copied the model directly from directory. Now let's integrate with MLflow so we can grab `production` grade trained model from the MLflow registry.


