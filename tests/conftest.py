import os
from types import SimpleNamespace

import pytest


# These must exist before importing src.handler: importing it builds the app graph.
@pytest.fixture(scope="session", autouse=True)
def test_environment():
    values = {
        "APP_ENV": "dev",
        "AWS_BASE_URL": "http://localhost:4566",
        "AWS_REGION": "us-east-1",
        "BUCKET_NAME": "image-uploader-test",
        "IMAGE_TABLE": "images-test",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_EC2_METADATA_DISABLED": "true",
    }
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    yield
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def lambda_context():
    return SimpleNamespace(aws_request_id="test-request-id")


@pytest.fixture
def config():
    from src.config import AwsConfig, Config, TableNames

    return Config(
        aws=AwsConfig(
            base_url="http://localhost:4566",
            region="us-east-1",
            bucket_name="image-uploader-test",
            table_names=TableNames(image_table="images-test"),
        )
    )
