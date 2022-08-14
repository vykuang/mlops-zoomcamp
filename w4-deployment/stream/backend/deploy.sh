#!/bin/sh
docker run -it --rm -p 9696:9696 \
    -v /home/kohada/.aws:/root/.aws \
    --env-file=.env \
    duration-prediction-webapp:v2
