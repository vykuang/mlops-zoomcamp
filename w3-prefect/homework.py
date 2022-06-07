import pandas as pd
import datetime
from pathlib import Path
import pickle

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from prefect import flow, task, get_run_logger
from prefect.task_runners import SequentialTaskRunner

# changing from a script run on terminal to a prefect deployment
from prefect.deployments import DeploymentSpec
# from prefect.orion.schemas.schedules import IntervalSchedule
from prefect.orion.schemas.schedules import CronSchedule
from prefect.flow_runners import SubprocessFlowRunner
from datetime import timedelta

# homework q2. parametrizing main with date
@task
def get_paths(date=None):
    """Returns the file paths for fhv trip data based on date supplied.
    file paths formatted as fhv_tripdata_2021-{month}.parquet
    
    Parameters:
    date: str
        Assumes format is in "yyyy-mm-dd"
        If None, defaults to current system date
        Month must be '03' or later

    Returns:
    train_path: str
        fhv trip data file path 2 months before `date`
    val_path: str
        fhv trip data file path 1 month before `date`
    """
    if not date:
        date = datetime.date.today()

    month = int(date.split('-')[1])

    
    logger = get_run_logger()
    if month > 2 & month <= 12:
        # two months prior for training
        train_path = f'../data/fhv_tripdata_2021-{month-2:02}.parquet'
        # prev month for validation
        val_path = f'../data/fhv_tripdata_2021-{month-1:02}.parquet'

        logger.info(f'training path:\n{train_path}')
        logger.info(f'validation path:\n{val_path}')
    
    else:
        logger.error('Supplied month must be 3 to 12')
        raise ValueError('Supplied month must be 3 to 12')
    return train_path, val_path

@task
def read_data(path):
    logger = get_run_logger()
    if Path(path).exists():
        df = pd.read_parquet(path)    
    else:
        logger.error(f'parquet file not found: {Path(path).name}')
        raise FileNotFoundError
    return df

@task
def prepare_features(df, categorical, train=True):
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    mean_duration = df.duration.mean()

    # replace print with logger
    logger = get_run_logger()
    if train:
        # print(f"The mean duration of training is {mean_duration}")
        logger.info(f"The mean duration of training is {mean_duration}")
    else:
        print(f"The mean duration of validation is {mean_duration}")
        logger.info(f"The mean duration of validation is {mean_duration}")
    
    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    return df

@task
def train_model(df, categorical):

    train_dicts = df[categorical].to_dict(orient='records')
    dv = DictVectorizer()
    X_train = dv.fit_transform(train_dicts) 
    y_train = df.duration.values

    logger = get_run_logger()
    logger.info(f"The shape of X_train is {X_train.shape}")
    logger.info(f"The DictVectorizer has {len(dv.feature_names_)} features")

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_train)
    mse = mean_squared_error(y_train, y_pred, squared=False)
    logger.info(f"The MSE of training is: {mse}")
    return lr, dv

@task
def run_model(df, categorical, dv, lr):
    val_dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(val_dicts) 
    y_pred = lr.predict(X_val)
    y_val = df.duration.values

    mse = mean_squared_error(y_val, y_pred, squared=False)

    logger = get_run_logger()
    logger.info(f"The MSE of validation is: {mse}")
    return

@flow(task_runner=SequentialTaskRunner())
def main(output_path: str = './models/',
         date: str = None,         
        #  train_path: str = '../data/fhv_tripdata_2021-01.parquet', 
        #  val_path: str = '../data/fhv_tripdata_2021-02.parquet',
    ):

    categorical = ['PUlocationID', 'DOlocationID']

    # Q1 - Feels like I needed to add .result() on every
    # func besides run_model and read_data before I could get it working
    train_path, val_path = get_paths(date).result()
    df_train = read_data(train_path)
    # homework q1. Add .result() to prepare_features
    df_train_processed = prepare_features(df_train, categorical).result()

    df_val = read_data(val_path)
    df_val_processed = prepare_features(df_val, categorical, False).result()

    # train the model
    # add .result() to prevent 
    # TypeError: cannot unpack non-iterable PrefectFuture object
    lr, dv = train_model(df_train_processed, categorical).result()

    # Q3 - pickling our model and dv obj within the main flow
    # use model-{yyyy-mm-dd}.bin and dv-{yyyy-mm-dd}.pkl format
    output_path = Path(output_path)
    if not output_path.exists():
        Path.mkdir(output_path)

    # dv.bin sized at 13,191 bytes
    with open(output_path / f'model-{date}.bin', 'wb') as model_out, \
         open(output_path / f'dv-{date}.bin', 'wb') as dv_out:
        pickle.dump(lr, model_out)
        pickle.dump(dv, dv_out)

    run_model(df_val_processed, categorical, dv, lr)

# Q2 - passing 2021-08-15 as date
# validation MSE was 11.637
# import argparse
# if __name__ == '__main__':
#     """Ran flow in CLI for the Q1-3"""
#     parser = argparse.ArgumentParser()
#     parser.add_argument(
#         '--output_path', '-o',
#         default='~/mlops-notes/w3-prefect/models/',
#         help='Output folder to store the serialized model and input transformer',
#     )    
#     parser.add_argument(
#         '--date', '-d',
#         default='',
#         help='Date in yyyy-mm-dd format for which to make the trip duration prediction',
#     )    
#     args = parser.parse_args()
#     main(args.output_path, args.date)

# Q5 after removing view filters, prefect has three (3) scheduled runs
DeploymentSpec(
    # the main func we defined above
    flow=main,
    name='model_training',
    # Q4: 9:00 AM, every 15th
    schedule=CronSchedule(
        # format: 'min h d_of_m mth d_of_w'
        cron='0 9 15 * *',
        timezone='America/New_York',
        ),
    # below is to run specifically on local storage
    # if not specified, default is universal
    flow_runner=SubprocessFlowRunner(),
    tags=['ml']
)

# After creating work-queue via web UI, view list of work-queues
# on CLI with prefect work-queue ls
