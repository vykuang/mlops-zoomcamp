from datetime import datetime

import batch
import pandas as pd


def dt(hour, minute, second=0):
    return datetime(2021, 1, 1, hour, minute, second)


def test_one():
    assert 1 == 1


def test_read():
    # test data
    data = [
        (None, None, dt(1, 2), dt(1, 10)),  # not valid
        (1, 1, dt(1, 2), dt(1, 10)),
        (1, 1, dt(1, 2, 0), dt(1, 2, 50)),  # < 1 min duration
        (1, 1, dt(1, 2, 0), dt(2, 2, 1)),
    ]

    columns = ["PUlocationID", "DOlocationID", "pickup_datetime", "dropOff_datetime"]
    df = pd.DataFrame(data, columns=columns)

    actual_df = batch.prepare_data(df)
    print(actual_df.to_json())
    # expected_df =
    assert len(actual_df) == 2
