import os
import pandas as pd
from datetime import datetime

def get_output_path(year, month):
    default_output_pattern = 's3://nyc-duration/fhv/fhv_tripdata_{year:04d}_{month:02d}.parquet'
    output_pattern = os.getenv('OUTPUT_FILE_PATTERN', default_output_pattern)
    return output_pattern.format(year=year, month=month)

def dt(hour, minute, second=0):
    return datetime(2021, 1, 1, hour, minute, second)

data = [
    (None, None, dt(1, 2), dt(1, 10)), # not valid
    (1, 1, dt(1, 2), dt(1, 10)),
    (1, 1, dt(1, 2, 0), dt(1, 2, 50)), # < 1 min duration
    (1, 1, dt(1, 2, 0), dt(2, 2, 1)),        
    ]

columns = ['PUlocationID', 'DOlocationID', 'pickup_datetime', 'dropOff_datetime']
df_input = pd.DataFrame(data, columns=columns)

S3_ENDPOINT_URL = 'http://127.0.0.1:4566'
options = {
    'client_kwargs': {
        'endpoint_url': S3_ENDPOINT_URL
    }
}
input_file = get_output_path(2021, 1)

df_input.to_parquet(
    # 'input_file.parquet',
    input_file,
    engine='pyarrow',
    compression=None,
    index=False,
    storage_options=options,
)