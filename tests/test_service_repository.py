from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.image_schemas import UploadImageFields, UploadImageFile
from src.repository import ImageRepository
from src.service import ImageService
from tests.fakes import MemoryDynamo, MemoryS3, MemoryTable


@pytest.fixture
def system(config):
    table = MemoryTable()
    clients = SimpleNamespace(s3_client=MemoryS3(), dynamodb_client=MemoryDynamo(table))
    repo = ImageRepository(clients)
    return ImageService(config, clients, repo), clients, table


def test_upload_persists_object_and_metadata(system, monkeypatch):
    service, clients, table = system
    monkeypatch.setattr("src.service.uuid.uuid4", lambda: "fixed-image-id")
    item = service.upload_image(UploadImageFields(user_id="u1"), UploadImageFile(filename="a.jpg", content_type="image/jpeg", content=b"image"))
    assert item["s3_key"] == "u1/fixed-image-id/a.jpg"
    assert clients.s3_client.objects[item["s3_key"]]["content"] == b"image"
    assert table.items[("USER#u1", "IMAGE#fixed-image-id")]["size"] == 5


def test_list_generates_and_accepts_pagination_tokens(system):
    service, _, table = system
    for image_id in ("1", "2", "3"):
        table.put_item(Item={"PK": "USER#u1", "SK": f"IMAGE#{image_id}", "image_id": image_id})
    first = service.list_images("u1", 2, None)
    assert [item["image_id"] for item in first["items"]] == ["1", "2"]
    assert first["next_token"]
    second = service.list_images("u1", 2, first["next_token"])
    assert [item["image_id"] for item in second["items"]] == ["3"]
    assert second["next_token"] is None


def test_get_url_and_delete_remove_both_resources(system):
    service, clients, table = system
    key = "u1/i1/a.jpg"
    clients.s3_client.upload_file(key, b"image", "image/jpeg")
    table.put_item(Item={"PK": "USER#u1", "SK": "IMAGE#i1", "s3_key": key})
    assert service.generate_presigned_url("u1", "i1")["url"].startswith("https://s3.test/")
    assert service.delete_image("u1", "i1") is True
    assert key in clients.s3_client.deleted
    assert table.get_item({"PK": "USER#u1", "SK": "IMAGE#i1"}) == {}


def test_delete_missing_image_raises_value_error(system):
    service, _, _ = system
    with pytest.raises(ValueError, match="Image not found"):
        service.delete_image("missing", "image")


def test_service_upload_reraises_storage_errors(config):
    clients = SimpleNamespace(s3_client=MagicMock(), dynamodb_client=MagicMock())
    clients.s3_client.upload_file.side_effect = RuntimeError("storage unavailable")
    service = ImageService(config, clients, MagicMock())
    with pytest.raises(RuntimeError, match="storage unavailable"):
        service.upload_image(UploadImageFields(user_id="u"), UploadImageFile(filename="a", content_type="x", content=b"1"))


def test_repository_uses_table_operations():
    table = MagicMock()
    clients = SimpleNamespace(dynamodb_client=SimpleNamespace(get_table=MagicMock(return_value=table)))
    repo = ImageRepository(clients)
    item, key = {"PK": "USER#u", "SK": "IMAGE#i"}, {"PK": "USER#u", "SK": "IMAGE#i"}
    repo.put_item("images", item)
    repo.get_item("images", key)
    repo.delete_item("images", key)
    table.put_item.assert_called_once_with(Item=item)
    table.get_item.assert_called_once_with(Key=key)
    table.delete_item.assert_called_once_with(Key=key)


def test_repository_list_passes_limit_and_start_key():
    table = MagicMock()
    table.query.return_value = {"Items": [{"image_id": "1"}], "LastEvaluatedKey": {"PK": "USER#u", "SK": "IMAGE#1"}}
    repo = ImageRepository(SimpleNamespace(dynamodb_client=SimpleNamespace(get_table=MagicMock(return_value=table))))
    items, next_key = repo.list_images("u", "images", 3, {"PK": "USER#u", "SK": "IMAGE#0"})
    assert items == [{"image_id": "1"}]
    assert next_key["SK"] == "IMAGE#1"
    assert table.query.call_args.kwargs["Limit"] == 3
    assert table.query.call_args.kwargs["ExclusiveStartKey"]["SK"] == "IMAGE#0"
