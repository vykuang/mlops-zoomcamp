#! /usr/bin/env python

'''
Batch scoring script to compare actual ride duration to predicted duration
'''
from cProfile import run
import os
import uuid
import argparse
import pandas as pd

from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline

import mlflow

# Use .env to parametrize our script
RUN_ID = os.getenv(key='RUN_ID', default='815e49bd6e69425d977f2042f7f74c97')
MLFLOW_HOST = os.getenv(key='MLFLOW_HOST', default='13.215.46.159')

MLFLOW_URI = f'http://{MLFLOW_HOST}:5000'
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("green-taxi-duration")

def load_model(run_id):
    logged_model = f's3://mlflow-artifacts-remote-1212/3/{run_id}/artifacts/model'
    model = mlflow.pyfunc.load_model(logged_model)
    return model

def read_dataframe(filename: str):
    df = pd.read_parquet(filename)

    # In this usage example, the target variable is usually
    # not present if we're simply applying the model,
    # vs training the model
    df['duration'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)]
    
    return df


def prepare_dictionaries(df: pd.DataFrame):
    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)

    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']
    categorical = ['PU_DO']
    numerical = ['trip_distance']
    dicts = df[categorical + numerical].to_dict(orient='records')
    return dicts

def apply_model(input_file, run_id, output_file):
    df = read_dataframe('../../data/green_tripdata_2021-01.parquet')
    # df = read_dataframe(input_file)

    # applying model, not training
    # df_val = read_dataframe('../../data/green_tripdata_2021-02.parquet')
    # target = 'duration'
    # y_train = df[target].values
    # y_val = df_val[target].values

    dicts = prepare_dictionaries(df)
    # dict_val = prepare_dictionaries(df_val)
    model = load_model(run_id)

    y_pred = model.predict(dicts)

    df_result = pd.DataFrame()
    df_result['ride_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df_result['lpep_pickup_datetime'] = df['lpep_pickup_datetime']
    df_result['PULocationID'] = df['PULocationID']
    df_result['DOLocationID'] = df['DOLocationID']
    df_result['actual_duration'] = df['duration']
    df_result['predicted_duration'] = y_pred
    df_result['diff'] = df_result['actual_duration'] - df_result['predicted_duration']
    df_result['model_version'] = run_id
    
    df_result.to_parquet(output_file, index=False)

    # with mlflow.start_run():
    #     params = dict(max_depth=20, n_estimators=100, min_samples_leaf=10, random_state=0)
    #     mlflow.log_params(params)

    #     # use pipeline to combine dict_vect and model into one object
    #     pipeline = make_pipeline(
    #         DictVectorizer(),
    #         RandomForestRegressor(**params, n_jobs=-1)
    #     )

    #     pipeline.predict(dicts)
    #     y_pred = pipeline.predict(dict_val)

    #     rmse = mean_squared_error(y_pred, y_val, squared=False)
    #     print(params, rmse)
    #     mlflow.log_metric('rmse', rmse)

    #     mlflow.sklearn.log_model(pipeline, artifact_path="model")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--taxi-type', '-t',
        default='green',
        help='fhv or green; defaults to green',
    )
    parser.add_argument(
        '--year', '-y',
        type=int,
        default=2021,
    )
    parser.add_argument(
        '--month', '-m',
        type=int,
        default=1,
    )
    parser.add_argument(
        '--run_id', '-i',
        type=str,
        default='815e49bd6e69425d977f2042f7f74c97'
    )
    args = parser.parse_args()
    input_file = f's3://nyc-tlc/trip data/{args.taxi_type}_tripdata_{args.year:04d}-{args.month:02d}.parquet'
    if not os.path.exists('./output'):
        os.mkdir('./output')
        
    output_file = f'./output/{args.taxi_type}-{args.year:04d}-{args.month:02d}.parquet'
    apply_model(input_file=input_file,
                run_id=args.run_id,
                output_file=output_file)