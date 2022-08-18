# Streaming Model Deployment with GCP Functions and Pub/Sub

A ride duration prediction model is deployed as both a web service, and as part of a streaming pipeline.

Process outline:

1. Request containing ride data (datetime, pickup/dropoff ID, distance, etc.) is POST'd to the web service container
2. The web service container (flask) will respond with two ride duration predictions
3. First prediction uses a model stored in AWS S3 bucket as MLflow artifact
4. The second prediction relies on the following streaming pipeline:
	1. Web service publishes the ride data as a message to GCP Pub/Sub
	2. The message triggers Cloud Functions, which runs a script to call a different model, also from S3 bucket, to make a ride duration prediction based on the received data
	3. Functions then publishes the prediction to another topic.
	4. Backend receives the streamed prediction via the subscriber client
5. Both results are returned to the initial request source.
