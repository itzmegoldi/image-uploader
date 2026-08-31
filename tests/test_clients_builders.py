from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.builder import get_clients, get_config, get_services, set_clients, set_config, set_services
from src.builder.clients import Clients
from src.builder.helpler import build_all_clients, build_all_services
from src.builder.repos import Repo
from src.builder.services import Services
from src.utils.dynamodb import DynamoDBClient
from src.utils.s3 import S3Client


def test_s3_wrapper_delegates_to_boto_client():
    with patch("src.utils.s3.boto3.client") as factory:
        boto = factory.return_value
        client = S3Client("bucket", "http://endpoint")
        client.upload_file("a", b"data", "image/png")
        client.generate_upload_url("a", "image/png", 12)
        client.generate_download_url("a", 13)
        client.delete("a")
    boto.put_object.assert_called_once_with(Bucket="bucket", Key="a", Body=b"data", ContentType="image/png")
    assert boto.generate_presigned_url.call_count == 2
    boto.delete_object.assert_called_once_with(Bucket="bucket", Key="a")


def test_dynamodb_wrapper_delegates_to_boto_clients():
    with patch("src.utils.dynamodb.boto3.resource") as resource, patch("src.utils.dynamodb.boto3.client") as factory:
        client = DynamoDBClient("us-east-1", "http://endpoint")
        table = client.get_table("images")
        client.put_item("images", {"PK": {"S": "x"}})
        client.get_item("images", {"PK": {"S": "x"}})
        client.query("images", "condition", limit=2, exclusive_start_key={"PK": {"S": "x"}})
    resource.return_value.Table.assert_called_once_with("images")
    assert table is resource.return_value.Table.return_value
    assert factory.return_value.put_item.called and factory.return_value.get_item.called and factory.return_value.query.called


def test_clients_and_builders_construct_full_graph(config):
    with patch("src.builder.clients.S3Client") as s3, patch("src.builder.clients.DynamoDBClient") as dynamo:
        clients = Clients().with_s3_client(config).with_dynamodb_client(config)
        assert clients.s3_client is s3.return_value
        assert clients.dynamodb_client is dynamo.return_value
        built = build_all_clients(config)
        assert built.s3_client is s3.return_value
    services = build_all_services(config, SimpleNamespace(s3_client=MagicMock(), dynamodb_client=MagicMock()))
    assert services.image_service.config is config
    assert isinstance(Repo().with_image_repo(MagicMock()).image_repo, object)
    assert isinstance(Services().with_image_service(config, MagicMock(), MagicMock()).image_service, object)


def test_builder_registry_and_unconfigured_errors(config):
    import src.builder as builder
    old = builder.__dict__.copy()
    try:
        builder.__dict__["__cfg"] = builder.__dict__["__svc"] = builder.__dict__["__clients"] = None
        for getter in (get_config, get_services, get_clients):
            with pytest.raises(ValueError):
                getter()
        set_config(config)
        set_clients("clients")
        set_services("services")
        assert get_config() is config
        assert get_clients() == "clients"
        assert get_services() == "services"
    finally:
        for name in ("__cfg", "__svc", "__clients"):
            builder.__dict__[name] = old[name]
