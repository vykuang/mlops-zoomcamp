# Monitoring ML services

Models degrade over time, and effective monitoring allows us to know when to take action. But more than just model accuracy, our deployed ML model are just like any other production software, with the added domain of machine learning and all the issues specific to it, e.g. data quality and model drift.

Four sectors of ML monitoring:

1. Service health: uptime, latency of the serving interface
2. Model performance: eval metric
3. Data quality and integrity - changes in source data?
4. Data drift and concept drift - does the underlying assumption of our model still apply?

More comprehensive monitoring may include

5. Performance by segment - extension of model performance, but with emphasis on certain target classes
6. Model bias/fairness
7. Outliers
8. Explainability

## How to monitor

Two different paradigms, depending on how the ML model is served:

### Batch monitoring

In addition to serving the model (via an orchestrated workflow), we could add a step in the pipeline that records our eval metric to a database, with which to build a report.

MongoDB is commonly used since the input/output formats of a ML webservice is often JSON, an unstructured data format.

A prefect flow could be scheduled to build a report based on monitoring data stored MongoDB.

### Online models

Besides serving the response to the user, an additional service could pull metrics metadata and feed to a realtime dashboard.

Evidently receives the input/output from the prediction_service, pushes metrics to Prometheus DB, and Grafana dashboards the results.

In our web service, before we return the `jsonify(results)`, we would save the in/out/metadata json to the Evidently service.

Note that batch and online monitoring are not mutually exclusive; it would still be wise to perform batch monitoring alongside online. Thus, we could also push the in/out/metadata json to the MongoDB and schedule an orchestrated report-building.

## Batch

Batch monitoring requires a *reference* dataset to compare with the latest batch of dataset in our MongoDB. The concept of *drift* only makes sense if we have a starting point to begin with.

## Running the services

All the services mentioned, i.e. MongoDB, evidently, prometheus, and grafana will be run as docker containers, requiring no additional installations
