import os


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):

    def __init__(self):
        self.download_folder = os.getenv("DOWNLOAD_FOLDER")
        self.new_folder = os.getenv("NEW_FOLDER")
        self.new_dynamo_table = os.getenv("NEW_DYNAMO_TABLE")
        # self.new_dynamo_table = os.getenv("NEW_DYNAMO_TABLE")
