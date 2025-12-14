# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import boto3
from botocore.exceptions import ClientError
from itemadapter import ItemAdapter


class WorkplacerelationsPipeline:
    def open_spider(self, spider):
        self.table = boto3.resource("dynamodb").Table("workplace_relations")

    def process_item(self, item, spider):
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(identifier)"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise e
        return item