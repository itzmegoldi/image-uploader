from email import policy
from email.parser import BytesParser
from typing import Any


def parse_multipart(
    body: bytes,
    content_type: str,
) -> dict[str, Any]:
    """
    Parse a multipart/form-data request.

    Returns:
    {
        "fields": {
            "user_id": "123",
            "type": "profile"
        },
        "files": {
            "image": {
                "filename": "photo.jpg",
                "content_type": "image/jpeg",
                "content": b"..."
            }
        }
    }
    """

    if not content_type.startswith("multipart/form-data"):
        raise ValueError("Request is not multipart/form-data")

    # Construct a fake MIME message because the email parser
    # expects headers + body.
    message = (
        f"Content-Type: {content_type}\r\n" "MIME-Version: 1.0\r\n" "\r\n"
    ).encode() + body

    msg = BytesParser(policy=policy.default).parsebytes(message)

    if not msg.is_multipart():
        raise ValueError("Invalid multipart request")

    fields: dict[str, str] = {}
    files: dict[str, dict[str, Any]] = {}

    for part in msg.iter_parts():
        content_disposition = part.get("Content-Disposition", "")

        if not content_disposition:
            continue

        name = part.get_param("name", header="Content-Disposition")

        if not name:
            continue

        filename = part.get_filename()

        if filename:
            files[name] = {
                "filename": filename,
                "content_type": part.get_content_type(),
                "content": part.get_payload(decode=True) or b"",
            }
        else:
            fields[name] = part.get_content()

    return {
        "fields": fields,
        "files": files,
    }
