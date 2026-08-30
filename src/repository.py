import json
from typing import Protocol

from boto3.dynamodb.conditions import Key
from src.builder.clients import Clients
from src.utils import logging

logger = logging.get_logger()


class IImageRepository(Protocol):

    def put_item(self, table_name: str, item: dict): ...
    def list_images(
        self,
        user_id: str,
        table_name: str,
        page_size: int,
        exclusive_start_key=None,
    ): ...
    def get_item(self, table_name: str, key: dict): ...
    def delete_item(self, table_name: str, key: dict): ...


class ImageRepository(IImageRepository):
    def __init__(self, clients: Clients):
        self.clients = clients

    def put_item(self, table_name: str, item: dict):
        table = self.clients.dynamodb_client.get_table(table_name)
        return table.put_item(Item=item)

    def list_images(
        self,
        user_id: str,
        table_name: str,
        page_size: int = 10,
        exclusive_start_key=None,
    ):
        try:
            params = {
                # "table_name": table_name,
                "KeyConditionExpression": Key("PK").eq(f"USER#{user_id}"),
                "Limit": page_size,
            }
            if exclusive_start_key:
                params["ExclusiveStartKey"] = exclusive_start_key

            table = self.clients.dynamodb_client.get_table(table_name)

            response = table.query(**params)

            logger.info(
                f"response {response}",
            )

            return (
                response.get("Items", []),
                response.get("LastEvaluatedKey"),
            )
        except Exception as e:
            raise e

    def get_item(self, table_name: str, key: dict):
        table = self.clients.dynamodb_client.get_table(table_name)
        return table.get_item(Key=key)

    def delete_item(self, table_name: str, key: dict):
        table = self.clients.dynamodb_client.get_table(table_name)
        return table.delete_item(Key=key)
