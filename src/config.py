from pydantic import BaseModel
from src.utils.config import ConfigMixIn


class TableNames(BaseModel):
    image_table: str


class AwsConfig(BaseModel):
    base_url: str
    region: str
    bucket_name: str
    table_names: TableNames


class Config(BaseModel, ConfigMixIn):
    aws: AwsConfig
