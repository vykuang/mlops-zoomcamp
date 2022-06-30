FROM agrigorev/zoomcamp-model:mlops-3.9.7-slim
# how it was built:
# FROM python:3.9.7-slim

# WORKDIR /app
# COPY [ "model2.bin", "model.bin" ]
RUN pip install --upgrade pip

RUN pip install pipenv
WORKDIR /app

# use existing .pickle file within the image
COPY [ "Pipfile", "Pipfile.lock", "starter.py", "./"]
RUN pipenv install --system --deploy
ENTRYPOINT [ "python", "starter.py", "-y", "2021", "-m", "4"]