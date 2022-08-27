# MLOps Best Practices

## Managing python versions with `pyenv`

Best not to simply upgrade to replace existing python installations since it may be part of a dependency chain. Instead, install new versions and manage with `pyenv`

### Installation

1. Can't use `pip`; instead, clone the repo into a directory of choice, `$HOME/.pyenv` is preferred.
2. Add `pyenv` command to `$PATH` in the usual suspects:
    * `~/.bashrc`
    * `~/.bash_profile`
    * `~/.profile`

New installations can be then be made via `pyenv install 3.9.12` or any other version we want. Note that there are some libraries that need to be installed separately, *prior to `pyenv install`*. See [Required build environment](https://github.com/pyenv/pyenv/wiki#suggested-build-environment). tldr, run this:

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

* Test\*.py must have **unique names** because `pytest` will import each test as top level module, since there is no package to derive the name from.
    * *Package* is defined as a directory containing `__init__.py`.

Approach 2 - Allowing test\*.py with same name:

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

## Code quality - linting and formatting

Use `pylint`; `pipenv install --dev pylint` to use in dev mode only, not in production. To use:

```bash
pylint file_to_check.py
```

Terminal will output the pylint evaluation.

Alternatively in vs code, run linter from cmd palette

### pylint config

By default there are a bunch of rules active that you may not care about, e.g. doc string for each fun, or snake_case naming style, or trailing newlines/whitespace.

Use `.pylintrc` to configure pylint behaviour. Alternatively `pyproject.toml` can also contain pylint config under the heading `[tool.pylint.messages_control]`:

```toml
[tool.pylint.messages_control]
disable = [
	"missing-function-docstring",
	"missing-final-newline"
]
```

Alternatively, inline comments can also control messages via `# pylint: disable=<some_rule>`. [See docs for more disabling options](https://pylint.pycqa.org/en/latest/user_guide/messages/message_control.html)

### Formatting with `black` and `isort`

Easy one first: `isort` formats the code imports in order of significance. Style thing.

`black` takes `pylint` one step further, by actually changing the code according to the rules. Use `black --diff . | less` to view the changes to be made before confirming.

### Git pre-commit hooks with Make files

So instead of typing all that every time before we commit:

```bash
black .
isort .
pylint .
pytest .
```

And perhaps forgetting a command or two, we can use `pre-commit` hooks so that those commands are automatically run each time we commit to our repo.

Install with `pipenv install --dev pre-commit`

In the repo home directory, or `mlops-notes/`, there is a `.git/hooks/` folder. If we include a `.pre-commit-config.yaml` file, it will run the contents of that file before each commit, using another file called `pre-commit`.

* Create a sample one with `pre-commit sample-config > .pre-commit-config.yaml`
* Create `pre-commit` with `pre-commit install` command. It will be placed inside `.git/hooks/`. This pre-commit config is not version controlled, and is specific per user, not by repo. Therefore not everybody committing to the same repo need the same pre-commit.
* `.pre-commit-config.yaml` can be modified to include pre-commit hooks for `black`, `isort`, `pylint`, and `pytest`. Google *pre-commit things_we_need_hooks_for*. Place the `.yaml` in the project root, same as `.git/`.

### Make and makefiles

If not installed, `sudo apt install make`. Confirm with `make --version`.

Manifests as a `Makefile` in our project root directory. Sample content:

```make
integration_test: test
	echo other_thing

quality_checks: integration_test
	isort .
	black .
	pylint .
```

Then, run `make quality_checks` will run all the commands under `quality_checks`, after running the dependency in `integration_test`.

Make use of variable names in makefiles - same syntax as bash:

```make
LOCAL-TAG=`date +"%Y-%m-%d-%H-%M"`
LOCAL_IMG_NAME="stream-model-duration:${LOCAL_TAG}"
```

Note the `+` following `date` is the `+FORMAT` flag for the date command.

Use it to

* perform formatting and linting checks
* pytests
* build test-docker images
* run integration tests
* publish to docker registry (optional)

Using makefiles allows all these things to be captured in version control.

## Terraform
