from src.utils.s3 import S3Client
from src.utils.dynamodb import DynamoDBClient


class Clients:
    def with_s3_client(self, config):

        self.s3_client = S3Client(config.aws.bucket_name, config.aws.base_url)
        return self

    def with_dynamodb_client(self, config):

        self.dynamodb_client = DynamoDBClient(config.aws.region, config.aws.base_url)
        return self
