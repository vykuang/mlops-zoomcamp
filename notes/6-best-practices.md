# MLOps Best Practices

## Managing python versions with `pyenv`

Best not to simply upgrade to replace existing python installations since it may be part of a dependency chain. Instead, install new versions and manage with `pyenv`

### Installation

1. Can't use `pip`; instead, clone the repo into a directory of choice, `$HOME/.pyenv` is preferred.
2. Add `pyenv` command to `$PATH` in the usual suspects: 
    * `~/.bashrc`
    * `~/.bash_profile`
    * `~/.profile`

New installations can be then be made via `pyenv install 3.9.12` or any other version we want. Note that there are some libraries that need to be installed separately, *prior to `pyenv install`. See [Required build environment](https://github.com/pyenv/pyenv/wiki#suggested-build-environment). tldr, run this:

```bash
sudo apt-get update; sudo apt-get install make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

Then do `pyenv install` so that the python installations will have access to the basic libraries

## Unit testing with `pytest`

### Project layout

Approach 1 - separating tests from application code

```
pyproject.toml
setup.cfg
mypkg/
    __init__.py
    app.py
    view.py
tests/
    test_app.py
    test_view.py
```

* Test*.py must have **unique names** because `pytest` will import each test as top level module, since there is no package to derive the name from.
    * *Package* is defined as a directory containing `__init__.py`.

Approach 2 - Allowing test*.py with same name:

```
pyproject.toml
setup.cfg
src/
    mypkg/
        __init__.py
        app.py
        view.py
tests/
    __init__.py
    foo/
        __init__.py
        test_view.py
    bar/
        __init__.py
        test_view.py
```

Even though there are two `test_view.py`, pytest imports them as `tests.foo.test_view` and `tests.bar.test_view`, allowing two duplicate test file names.

This is the approach used in the mlops zoomcamp.

However the application code must be tucked inside `/src/` to allow tools like `tox` to test the package in a virtual env

## Testing cloud services with `LocalStack`

### Installation

CLI is an option but we'll use docker

Pull from docker hub with tag `localstack/localstack:1.0.0`.

* `docker run --rm -it -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack:1.0.0`
* Comes with `awscli` and `localstack` cli in the form of `awslocal`, which is a thin wrapper for `aws`
* creating a bucket in aws: 

```bash
aws s3api create-bucket \
    --bucket my-bucket \
    --region us-east-1
```

* In localstack, use `awslocal` instead:

```bash
awslocal s3api create-bucket \
    --bucket my-bucket \
    --region us-east-1
```

* tutorial uses `aws s3 mb s3://my-bucket`, which we can also wrap with `awslocal`.

### Read localstack S3 with pandas

In our `read_data()` function, we use `pd.read_parquet` to read directly from S3. With localstack, we can mock the S3 connection and test offline.

Do so by specifying endpoint url:

```python
options = {
    'client_kwargs': {
        'endpoint_url': S3_ENDPOINT_URL
    }
}

df = pd.read_parquet('s3://bucket/file.parquet', storage_options=options)
# Conversely, writing to localstack S3:
df_input.to_parquet(
    's3://nyc-duration/taxi_type=fhv/year=2021/month=01/predictions.parquet',
    engine='pyarrow',
    compression=None,
    index=False,
    storage_options=options,
)
```

For localstack, our endpoint url is the `http://127.0.0.1:4566`, our localstack gateway.
