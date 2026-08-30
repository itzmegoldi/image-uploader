import boto3


class S3Client:

    def __init__(self, bucket_name, endpoint_url):
        self.bucket_name = bucket_name
        self.client = boto3.client("s3", endpoint_url=endpoint_url)

    def upload_file(
        self,
        key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    def generate_upload_url(self, key, content_type, expires_in=3600):
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    def generate_download_url(self, key, expires_in=3600):
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket_name, Key=key)
