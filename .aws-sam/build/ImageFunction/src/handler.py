import base64
import json
import time
from decimal import Decimal

from pydantic import ValidationError
from src.builder import get_services
from src.builder.helpler import fetch_config_and_build_services
from src.image_schemas import (
    GetImageUrlRequest,
    ListImagesRequest,
    UploadImageFields,
    UploadImageFile,
)
from src.utils import logging

from src.utils.multipart_processor import parse_multipart

fetch_config_and_build_services()
logger = logging.get_logger()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)

        return super().default(obj)


def get_image_service():
    return get_services().image_service


def log_handler(event, context, message):
    request_id = context.aws_request_id
    timestamp = int(time.time() * 1000)
    logger.info(
        message,
        extra={
            "request_id": request_id,
            "extra_data": {
                "path": event.get("path"),
                "method": event.get("httpMethod"),
                "time": timestamp,
            },
        },
    )


def upload_image(event, context):
    try:
        headers = {
            key.lower(): value for key, value in event.get("headers", {}).items()
        }

        content_type = headers.get("content-type")

        body = event.get("body", "")

        if event.get("isBase64Encoded"):
            body = base64.b64decode(body)
        else:
            body = body.encode()

        multipart = parse_multipart(
            body=body,
            content_type=content_type,
        )

        fields = multipart["fields"]
        files = multipart["files"]

        upload_fields = UploadImageFields.model_validate(fields)

        image_data = files.get("image", None)
        if not image_data:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Image file is required"}),
            }

        upload_file = UploadImageFile.model_validate(image_data)

        service = get_image_service()
        item = service.upload_image(fields=upload_fields, files=upload_file)

        return {
            "statusCode": 201,
            "body": json.dumps({"success": True, "item": item}, cls=DecimalEncoder),
        }
    except ValidationError as e:
        log_handler(event, context, f"Request validation error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid request", "details": e.json()}),
        }
    except Exception as e:
        log_handler(event, context, f"Failed to upload image: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def list_images(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}

        request = ListImagesRequest(
            user_id=query_params.get("user_id"),
            page_size=query_params.get(
                "page_size",
                20,
            ),
            next_token=query_params.get("next_token"),
        )

        service = get_image_service()

        result = service.list_images(
            user_id=request.user_id,
            page_size=request.page_size,
            next_token=request.next_token,
        )

        # ===========Request Completion logger ================
        log_handler(
            event,
            context,
            "Complete multipart request.",
        )
        # ===========Request Completion logger ================

        return {
            "statusCode": 200,
            "body": json.dumps(result, cls=DecimalEncoder),
        }

    except ValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "Invalid request",
                    "details": e.json(),
                }
            ),
        }

    except Exception as e:
        log_handler(
            event,
            context,
            f"Failed to list images: {e}",
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": f"Internal server error {e}",
                }
            ),
        }


def get_image_url(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}

        user_id = query_params.get("user_id")
        image_id = query_params.get("image_id")

        request = GetImageUrlRequest(
            user_id=user_id,
            image_id=image_id,
        )

        service = get_image_service()

        result = service.generate_presigned_url(
            user_id=user_id,
            image_id=image_id,
        )
        # result = {}

        # ===========Request Completion logger ================
        log_handler(
            event,
            context,
            "Complete image request.",
        )
        # ===========Request Completion logger ================

        return {
            "statusCode": 201,
            "body": json.dumps(result, cls=DecimalEncoder),
        }

    except ValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "Invalid request",
                    "details": e.json(),
                }
            ),
        }

    except Exception as e:
        log_handler(
            event,
            context,
            f"Failed to generate image url: {e}",
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": f"Internal server error {e}",
                }
            ),
        }


def delete_image(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}

        user_id = query_params.get("user_id")
        image_id = query_params.get("image_id")

        request = GetImageUrlRequest(
            user_id=user_id,
            image_id=image_id,
        )

        service = get_image_service()

        result = service.delete_image(
            user_id=user_id,
            image_id=image_id,
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "success": result,
                },
                cls=DecimalEncoder,
            ),
        }

    except ValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "Invalid request",
                    "details": e.json(),
                }
            ),
        }

    except Exception as e:
        log_handler(
            event,
            context,
            f"Failed to generate image url: {e}",
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": f"Internal server error {e}",
                }
            ),
        }


def api_handler(event, context):
    method = event.get("httpMethod")
    path = event.get("resource")

    log_handler(
        event,
        context,
        f"Received request: {method} {path}",
    )

    if method == "POST" and path == "/upload-image":
        return upload_image(event, context)

    if method == "GET" and path == "/list-images":
        return list_images(event, context)

    if method == "GET" and path == "/get-download-url":
        return get_image_url(event, context)

    if method == "DELETE" and path == "/delete-image":
        return delete_image(event, context)

    log_handler(
        event,
        context,
        f"Resource Not found: {method} {path}",
    )

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Resource Not found"}),
    }
