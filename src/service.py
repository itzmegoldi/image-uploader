import uuid
from datetime import datetime
from typing import Protocol

from src.builder.clients import Clients
from src.config import Config
from src.image_schemas import UploadImageFields, UploadImageFile
from src.repository import IImageRepository

from src.utils import logging
from src.utils.common import decode_token, encode_token

logger = logging.get_logger()


class IImageService(Protocol):
    def upload_image(self, fields, files): ...
    def list_images(self, user_id, page_size, next_token): ...
    def generate_presigned_url(self, user_id, image_id): ...
    def delete_image(self, user_id, image_id): ...


class ImageService(IImageService):
    def __init__(self, config: Config, clients: Clients, repo: IImageRepository):
        self.config = config
        self.clients = clients
        self.repo = repo
        self.image_table = config.aws.table_names.image_table

    def _build_s3_key(self, filename, image_id, user_id):
        return f"{user_id}/{image_id}/{filename}"

    def upload_image(self, fields: UploadImageFields, files: UploadImageFile):
        try:
            image_id = str(uuid.uuid4())
            now = int(datetime.now().timestamp())

            s3_key = self._build_s3_key(
                filename=files.filename,
                image_id=image_id,
                user_id=fields.user_id,
            )

            image_data = {
                "PK": f"USER#{fields.user_id}",
                "SK": f"IMAGE#{image_id}",
                "image_id": image_id,
                "user_id": fields.user_id,
                "filename": files.filename,
                "content_type": files.content_type,
                "size": files.size,
                "s3_key": s3_key,
                "created_at": now,
                "updated_at": now,
            }

            self.clients.s3_client.upload_file(
                key=s3_key,
                content=files.content,
                content_type=files.content_type,
            )

            self.repo.put_item(
                item=image_data,
                table_name=self.image_table,
            )

            return image_data
        except Exception as e:
            logger.error(
                f"upload image service error {e}",
            )
            raise e

    def list_images(
        self,
        user_id,
        page_size,
        next_token=None,
    ):

        start_key = None

        if next_token:
            start_key = decode_token(next_token)

        items, last_key = self.repo.list_images(
            user_id=user_id,
            table_name=self.image_table,
            page_size=page_size,
            exclusive_start_key=start_key,
        )

        logger.info(
            f"items {type(items)}",
            extra={
                "user_id": user_id,
                "page_size": page_size,
                "next_token": next_token,
            },
        )

        return {
            "items": items,
            "page_size": page_size,
            "next_token": (encode_token(last_key) if last_key else None),
        }

    def generate_presigned_url(self, user_id, image_id):
        response = self.repo.get_item(
            table_name=self.image_table,
            key={
                "PK": f"USER#{user_id}",
                "SK": f"IMAGE#{image_id}",
            },
        )
        item = response.get("Item")

        s3_key = item.get("s3_key", "")

        pre_signed_url = self.clients.s3_client.generate_download_url(
            key=s3_key,
        )

        return {
            "url": pre_signed_url,
        }

    def delete_image(self, user_id, image_id):
        response = self.repo.get_item(
            table_name=self.image_table,
            key={
                "PK": f"USER#{user_id}",
                "SK": f"IMAGE#{image_id}",
            },
        )
        item = response.get("Item")

        if not item:
            raise ValueError("Image not found")

        s3_key = item.get("s3_key", "")

        self.clients.s3_client.delete(
            key=s3_key,
        )

        self.repo.delete_item(
            table_name=self.image_table,
            key={
                "PK": f"USER#{user_id}",
                "SK": f"IMAGE#{image_id}",
            },
        )

        return True
