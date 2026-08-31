class MemoryS3:
    def __init__(self):
        self.objects = {}
        self.deleted = []

    def upload_file(self, key, content, content_type):
        self.objects[key] = {"content": content, "content_type": content_type}

    def generate_download_url(self, key, expires_in=3600):
        if key not in self.objects:
            raise KeyError(key)
        return f"https://s3.test/{key}?expires={expires_in}"

    def delete(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)


class MemoryTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[(Item["PK"], Item["SK"])] = Item.copy()
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def get_item(self, Key):
        item = self.items.get((Key["PK"], Key["SK"]))
        return {"Item": item.copy()} if item else {}

    def delete_item(self, Key):
        self.items.pop((Key["PK"], Key["SK"]), None)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def query(self, KeyConditionExpression, Limit, ExclusiveStartKey=None):
        # boto3 condition objects retain the comparison literal in _values.
        partition_key = KeyConditionExpression._values[1]
        matches = [item.copy() for (pk, _), item in self.items.items() if pk == partition_key]
        matches.sort(key=lambda item: item["SK"])
        if ExclusiveStartKey:
            start = (ExclusiveStartKey["PK"], ExclusiveStartKey["SK"])
            matches = [item for item in matches if (item["PK"], item["SK"]) > start]
        response = {"Items": matches[:Limit]}
        if len(matches) > Limit:
            item = matches[Limit - 1]
            response["LastEvaluatedKey"] = {"PK": item["PK"], "SK": item["SK"]}
        return response


class MemoryDynamo:
    def __init__(self, table):
        self.table = table

    def get_table(self, table_name):
        return self.table
