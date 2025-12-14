# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
import os
import boto3
from botocore.exceptions import ClientError
from itemadapter import ItemAdapter
import requests


class WorkplacerelationsPipeline:
    def open_spider(self, spider):
        self.table = boto3.resource("dynamodb").Table("workplace_relations")
        self.files_store = spider.settings.get("FILES_STORE", "downloaded_files")
        os.makedirs(self.files_store, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        downloaded_files = []
        links = adapter.get("links", [])
        for link in links:
            try:
                local_path = self.download_file(link)
                file_hash = self.calculate_hash(local_path)
                downloaded_files.append({
                    "url": link,
                    "path": local_path,
                    "hash": file_hash
                })
            except Exception as e:
                spider.logger.warning(f"Failed to download {link}: {e}")

        adapter["downloaded_files"] = downloaded_files

        # push to DynamoDB
        try:
            self.table.put_item(
                Item=dict(adapter),
                ConditionExpression="attribute_not_exists(identifier)"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise e

        return item

    def download_file(self, url):
        filename = url.split("/")[-1]
        local_path = os.path.join(self.files_store, filename)

        # Skip download if file already exists
        if os.path.exists(local_path):
            return local_path

        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        return local_path

    def calculate_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()