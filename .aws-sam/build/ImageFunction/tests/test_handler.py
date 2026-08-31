import base64
import json
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def handler():
    # Imported after the autouse environment fixture has built the test config.
    import src.handler
    return src.handler


def multipart_event(include_image=True, encoded=False):
    boundary = "TestBoundary"
    parts = [b'--TestBoundary\r\nContent-Disposition: form-data; name="user_id"\r\n\r\nu1\r\n']
    if include_image:
        parts.append(b'--TestBoundary\r\nContent-Disposition: form-data; name="image"; filename="photo.jpg"\r\nContent-Type: image/jpeg\r\n\r\nimage-data\r\n')
    body = b"".join(parts) + b"--TestBoundary--\r\n"
    return {
        "httpMethod": "POST", "resource": "/upload-image", "path": "/upload-image",
        "headers": {"CONTENT-TYPE": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode() if encoded else body.decode(),
        "isBase64Encoded": encoded,
    }


def response_body(response):
    return json.loads(response["body"])


def test_decimal_encoder(handler):
    assert json.dumps({"a": Decimal("1"), "b": Decimal("1.5")}, cls=handler.DecimalEncoder) == '{"a": 1, "b": 1.5}'


def test_upload_success_plain_and_base64(handler, lambda_context, monkeypatch):
    service = MagicMock()
    service.upload_image.return_value = {"size": Decimal("2"), "id": "i"}
    monkeypatch.setattr(handler, "get_image_service", lambda: service)
    for encoded in (False, True):
        response = handler.upload_image(multipart_event(encoded=encoded), lambda_context)
        assert response["statusCode"] == 201
        assert response_body(response)["item"]["size"] == 2
    assert service.upload_image.call_count == 2


def test_upload_missing_file_validation_and_unexpected_error(handler, lambda_context, monkeypatch):
    monkeypatch.setattr(handler, "get_image_service", lambda: MagicMock())
    assert handler.upload_image(multipart_event(include_image=False), lambda_context)["statusCode"] == 400
    invalid = multipart_event()
    invalid["body"] = "not multipart"
    assert handler.upload_image(invalid, lambda_context)["statusCode"] == 500
    failing = MagicMock()
    failing.upload_image.side_effect = RuntimeError("failed upload")
    monkeypatch.setattr(handler, "get_image_service", lambda: failing)
    response = handler.upload_image(multipart_event(), lambda_context)
    assert response["statusCode"] == 500
    assert response_body(response)["error"] == "failed upload"


@pytest.mark.parametrize("function,method,path,service_method,success_status", [
    ("list_images", "GET", "/list-images", "list_images", 200),
    ("get_image_url", "GET", "/get-download-url", "generate_presigned_url", 201),
    ("delete_image", "DELETE", "/delete-image", "delete_image", 200),
])
def test_query_handlers_success(handler, lambda_context, monkeypatch, function, method, path, service_method, success_status):
    service = MagicMock()
    getattr(service, service_method).return_value = True if function == "delete_image" else {"items": [], "url": "https://url"}
    monkeypatch.setattr(handler, "get_image_service", lambda: service)
    event = {"httpMethod": method, "resource": path, "path": path, "queryStringParameters": {"user_id": "u", "image_id": "i", "page_size": "2"}}
    response = getattr(handler, function)(event, lambda_context)
    assert response["statusCode"] == success_status
    if function == "delete_image":
        assert response_body(response) == {"success": True}


@pytest.mark.parametrize("function", ["list_images", "get_image_url", "delete_image"])
def test_query_handlers_validation_and_service_errors(handler, lambda_context, monkeypatch, function):
    fn = getattr(handler, function)
    missing = {"queryStringParameters": {}}
    assert fn(missing, lambda_context)["statusCode"] == 400
    service = MagicMock()
    method = {"list_images": "list_images", "get_image_url": "generate_presigned_url", "delete_image": "delete_image"}[function]
    getattr(service, method).side_effect = RuntimeError("boom")
    monkeypatch.setattr(handler, "get_image_service", lambda: service)
    event = {"path": "/x", "httpMethod": "GET", "queryStringParameters": {"user_id": "u", "image_id": "i"}}
    assert fn(event, lambda_context)["statusCode"] == 500


def test_api_handler_routes_and_404(handler, lambda_context, monkeypatch):
    routes = {
        ("POST", "/upload-image"): "upload_image", ("GET", "/list-images"): "list_images",
        ("GET", "/get-download-url"): "get_image_url", ("DELETE", "/delete-image"): "delete_image",
    }
    for (method, path), name in routes.items():
        target = MagicMock(return_value={"statusCode": 299})
        monkeypatch.setattr(handler, name, target)
        event = {"httpMethod": method, "resource": path, "path": path}
        assert handler.api_handler(event, lambda_context)["statusCode"] == 299
        target.assert_called_once_with(event, lambda_context)
    response = handler.api_handler({"httpMethod": "PATCH", "resource": "/none", "path": "/none"}, lambda_context)
    assert response["statusCode"] == 404
