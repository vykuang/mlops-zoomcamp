import argparse
from pathlib import Path
import pickle

import mlflow
import numpy as np

from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
  
def load_pickle(filename: str):
    with open(filename, "rb") as f_in:
        return pickle.load(f_in)


def run(data_path, tracking_uri, num_trials):

    dv = load_pickle(data_path / 'dv.pkl')
    X_train, y_train = load_pickle(data_path / 'train.pkl')
    X_valid, y_valid = load_pickle(data_path / 'valid.pkl')

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    else:
        mlflow.set_tracking_uri("sqlite:///mlflow.db")

    mlflow.set_experiment("nyc-taxi-experiment")
    
    # mlflow.sklearn.autolog()
    def objective(params):
        with mlflow.start_run():
            mlflow.set_tags(
                {'estimator_name':'RandomForestRegressor',
                 'estimator_class':'sklearn.ensemble._forest.RandomForestRegressor'}
            )
            mlflow.log_params(params)

            rf = RandomForestRegressor(**params)
            rf.fit(X_train, y_train)

            mlflow.sklearn.log_model(rf, artifact_path='model')
            y_pred = rf.predict(X_valid)
            rmse = mean_squared_error(y_valid, y_pred, squared=False)
            mlflow.log_metric('rmse', rmse)

            with open(data_path / 'dict_vectorizer.bin', 'wb') as f_out:
                pickle.dump(dv, f_out)
            
            # accepts str path only
            mlflow.log_artifact(str(data_path / 'dict_vectorizer.bin'))

        return {'loss': rmse, 'status': STATUS_OK}

    search_space = {
        'max_depth': scope.int(hp.quniform('max_depth', 1, 20, 1)),
        'n_estimators': scope.int(hp.quniform('n_estimators', 10, 50, 1)),
        'min_samples_split': scope.int(hp.quniform('min_samples_split', 2, 10, 1)),
        'min_samples_leaf': scope.int(hp.quniform('min_samples_leaf', 1, 4, 1)),
        'random_state': 42
    }

    rstate = np.random.default_rng(42)  # for reproducible results

    fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=num_trials,
        trials=Trials(),
        rstate=rstate
    )

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_path",
        default="../data/output",
        type=Path,
        help="the location where the processed NYC taxi trip data was saved."
    )
    parser.add_argument(
        "--tracking_uri", "-t",
        default=None,
        help="Host:port if remote; leave none for local mlflow.db file"
    )
    parser.add_argument(
        "--max_evals",
        default=50,
        type=int,
        help="the number of parameter evaluations for the optimizer to explore."
    )
    args = parser.parse_args()

    run(
        args.data_path, 
        args.tracking_uri, 
        args.max_evals
        )
