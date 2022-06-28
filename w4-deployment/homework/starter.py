#!/usr/bin/env python
# coding: utf-8


import argparse
import pickle
import os

import pandas as pd

def read_data(filename, year, month):
    df = pd.read_parquet(filename)
    
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()
    
    df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')

    categorical = ['PUlocationID', 'DOlocationID']
    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    dicts = df[categorical].to_dict(orient='records')
    return df, dicts

def get_paths(year, month):
    input_file = f's3://nyc-tlc/trip data/fhv_tripdata_{year:04d}-{month:02d}.parquet'

    EVAL_S3_STORE = os.getenv(key='EVAL_S3_STORE', 
                            default='s3://nyc-duration-predict-vk')
    output_file = f'{EVAL_S3_STORE}/fhv_tripdata_{year:04d}-{month:02d}.parquet'

    return input_file, output_file


def apply_model(df_taxi, dicts):
    with open('model.bin', 'rb') as f_in:
        dv, lr = pickle.load(f_in)

    X_val = dv.transform(dicts)
    y_pred = lr.predict(X_val)

    print(y_pred.mean())

    
    df_result = pd.DataFrame()
    df_result['ride_id'] = df_taxi['ride_id']
    # df_result = df.copy()
    df_result['pred'] = y_pred
    
    return df_result


def save_output(df_result, output_file):
    df_result.to_parquet(
        output_file,
        engine='pyarrow',
        compression=None,
        index=False,
    )

def run(year, month):    
    input_file, output_file = get_paths(year, month)
    df_taxi, dicts = read_data(input_file, year, month)
    df_result = apply_model(df_taxi, dicts)
    save_output(df_result, output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--year', '-y',
        default=2021,
        type=int,
        help='Year from which to retrieve fhv taxi data',
    )
    parser.add_argument(
        '--month', '-m',
        default=3,
        type=int,
        help='Month from which to retrieve fhv taxi data',
    )
    args = parser.parse_args()
    run(args.year, args.month)
