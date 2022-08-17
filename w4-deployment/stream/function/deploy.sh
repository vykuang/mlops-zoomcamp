#!/usr/bin/env bash
gcloud functions deploy predict_duration \
    --trigger-topic $BACKEND_PUSH_STREAM \
    --env-vars-file=".env.yaml" \
    --runtime=python39 \
    --set-secrets='AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID:latest,' \
    --set-secrets='AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY:latest'
    

    
    # --set-env-vars BACKEND_PULL_STREAM=$BACKEND_PULL_STREAM \
    # --set-env-vars PROJECT_ID=$PROJECT_ID \
    # --set-env-vars AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    # --set-env-vars AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \