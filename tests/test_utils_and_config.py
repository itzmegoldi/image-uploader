import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Config
from src.image_schemas import GetImageUrlRequest, ListImagesRequest, UploadImageFields, UploadImageFile
from src.utils.common import decode_token, encode_token
from src.utils.config import EnvNotSetException, get_env_key_value, load_and_merge_from_yaml, process_yaml_data, recursive_merge
from src.utils.multipart_processor import parse_multipart


def test_token_round_trip_and_invalid_token():
    key = {"PK": "USER#1", "SK": "IMAGE#1"}
    assert decode_token(encode_token(key)) == key
    with pytest.raises(Exception):
        decode_token("not-a-token")


def test_config_env_processing(monkeypatch):
    monkeypatch.setenv("TEST_VALUE", "resolved")
    assert get_env_key_value(r'\$env\["([^"]+)"\]', '$env["TEST_VALUE"]') == (True, "TEST_VALUE", "resolved")
    assert get_env_key_value(r'\$env\["([^"]+)"\]', "plain") == (False, "", None)
    assert get_env_key_value(r'\$env\["([^"]+)"\]', '$env["MISSING"]', strict=False)[2] == '$env["MISSING"]'
    with pytest.raises(EnvNotSetException):
        get_env_key_value(r'\$env\["([^"]+)"\]', '$env["MISSING"]')

    data = {"one": '$env["TEST_VALUE"]', "nested": [{"two": '$env["TEST_VALUE"]'}]}
    process_yaml_data(data)
    assert data == {"one": "resolved", "nested": [{"two": "resolved"}]}


def test_yaml_loading_merging_and_config(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_BUCKET", "bucket")
    (tmp_path / "test.yaml").write_text('aws:\n  base_url: http://localhost\n  region: us-east-1\n  bucket_name: $env["TEST_BUCKET"]\n  table_names:\n    image_table: images\n')
    loaded = load_and_merge_from_yaml(str(tmp_path), "test")
    assert loaded["aws"]["bucket_name"] == "bucket"
    assert Config.from_yaml(str(tmp_path), "test").aws.table_names.image_table == "images"
    assert recursive_merge({"a": [1], "b": {"x": 1}}, {"a": [2], "b": {"y": 2}}) == {"a": [1, 2], "b": {"x": 1, "y": 2}}


def test_multipart_parser_success_and_errors():
    boundary = "Boundary"
    body = (b"--Boundary\r\nContent-Disposition: form-data; name=\"user_id\"\r\n\r\nuser-1\r\n"
            b"--Boundary\r\nContent-Disposition: form-data; name=\"image\"; filename=\"cat.jpg\"\r\nContent-Type: image/jpeg\r\n\r\nbytes\r\n--Boundary--\r\n")
    parsed = parse_multipart(body, f"multipart/form-data; boundary={boundary}")
    assert parsed["fields"] == {"user_id": "user-1"}
    assert parsed["files"]["image"]["content"] == b"bytes"
    with pytest.raises(ValueError, match="multipart/form-data"):
        parse_multipart(b"x", "application/json")
    with pytest.raises(ValueError, match="Invalid multipart"):
        parse_multipart(b"x", "multipart/form-data; boundary=x")


def test_image_schema_validation_and_file_size():
    assert UploadImageFields(user_id=" person ").user_id == "person"
    assert UploadImageFile(filename="a.png", content_type="image/png", content=b"abc").size == 3
    assert ListImagesRequest(user_id="u").page_size == 10
    assert GetImageUrlRequest(user_id="u", image_id="i").image_id == "i"
    with pytest.raises(ValidationError):
        UploadImageFile(filename="", content_type="image/png", content=b"")
    with pytest.raises(ValidationError):
        ListImagesRequest(user_id="u", page_size=101)
    with pytest.raises(ValidationError):
        GetImageUrlRequest(user_id="", image_id="i")
