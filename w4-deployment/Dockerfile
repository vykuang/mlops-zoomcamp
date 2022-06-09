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