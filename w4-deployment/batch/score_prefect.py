#! /usr/bin/env python

'''
Batch scoring script to compare actual ride duration to predicted duration
'''
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import uuid
import argparse
import pandas as pd

from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline

import mlflow
from prefect import task
from prefect import get_run_logger
from prefect import flow
from prefect.context import get_run_context

# Use .env to parametrize our script
# RUN_ID = os.getenv(key='RUN_ID', default='815e49bd6e69425d977f2042f7f74c97')
MLFLOW_HOST = os.getenv(key='MLFLOW_HOST', default='13.215.46.159')
EVAL_S3_STORE = os.getenv(key='EVAL_S3_STORE', 
                          default='s3://nyc-duration-predict-vk')

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
    df['ride_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    return df

def prepare_dictionaries(df: pd.DataFrame):
    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)

    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']
    categorical = ['PU_DO']
    numerical = ['trip_distance']
    dicts = df[categorical + numerical].to_dict(orient='records')
    return dicts

@task
def apply_model(input_file, run_id, output_file):
    # df = read_dataframe('../../data/green_tripdata_2021-01.parquet')
    logger = get_run_logger()

    logger.info(f'reading from {input_file}')
    df = read_dataframe(input_file)

    # applying model, not training
    # df_val = read_dataframe('../../data/green_tripdata_2021-02.parquet')
    # target = 'duration'
    # y_train = df[target].values
    # y_val = df_val[target].values

    dicts = prepare_dictionaries(df)
    # dict_val = prepare_dictionaries(df_val)
    logger.info(f'loading the model with RUN_ID={run_id}...')
    model = load_model(run_id)

    logger.info(f'applying the model...')
    y_pred = model.predict(dicts)

    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['lpep_pickup_datetime'] = df['lpep_pickup_datetime']
    df_result['PULocationID'] = df['PULocationID']
    df_result['DOLocationID'] = df['DOLocationID']
    df_result['actual_duration'] = df['duration']
    df_result['predicted_duration'] = y_pred
    df_result['diff'] = df_result['actual_duration'] - df_result['predicted_duration']
    df_result['model_version'] = run_id
    
    logger.info(f'saving the result to {output_file}...')
    df_result.to_parquet(output_file, index=False)

    return output_file

@flow
def ride_duration_prediction(
    taxi_type: str, 
    run_id: str,
    run_date: datetime=None):

    if not run_date:
        ctx = get_run_context()
        run_date = ctx.flow_run.expected_start_time

    # if date is june, need data from may, for example
    prev_month = run_date - relativedelta(months=1)
    year = prev_month.year
    month = prev_month.month
    # input_file = f's3://nyc-tlc/trip data/{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet'
    input_file = f'https://d37ci6vzurychx.cloudfront.net/trip-data/{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet'
    # if not os.path.exists('./output'):
    #     os.mkdir('./output')
        
    # output_file = f'./output/{args.taxi_type}-{args.year:04d}-{args.month:02d}.parquet'
    
    output_file = f'{EVAL_S3_STORE}/{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet'
    apply_model(input_file=input_file,
                run_id=run_id,
                output_file=output_file)

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
        default=3,
    )
    parser.add_argument(
        '--run_id', '-i',
        type=str,
        default='815e49bd6e69425d977f2042f7f74c97'
    )
    args = parser.parse_args()
    ride_duration_prediction(
        taxi_type=args.taxi_type, 
        run_id=args.run_id, 
        run_date=datetime(year=args.year, month=args.month, day=1),
    )