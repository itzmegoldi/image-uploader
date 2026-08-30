import boto3


class DynamoDBClient:

    def __init__(self, region, endpoint_url):
        self.resource = boto3.resource(
            "dynamodb",
            region_name=region,
            endpoint_url=endpoint_url,
        )
        self.client = boto3.client(
            "dynamodb",
            region_name=region,
            endpoint_url=endpoint_url,
        )

    def get_table(self, table_name):
        return self.resource.Table(table_name)

    def put_item(self, table_name, item):
        return self.client.put_item(
            TableName=table_name,
            Item=item,
        )

    def get_item(self, table_name, key):
        return self.client.get_item(
            TableName=table_name,
            Key=key,
        )

    def query(
        self,
        table_name,
        key_condition_expression,
        limit=None,
        exclusive_start_key=None,
    ):
        params = {
            "TableName": table_name,
            "KeyConditionExpression": key_condition_expression,
        }

        if limit:
            params["Limit"] = limit

        if exclusive_start_key:
            params["ExclusiveStartKey"] = exclusive_start_key

        return self.client.query(**params)
