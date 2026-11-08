from pymongo import MongoClient


class MongoStorage:
    def __init__(self, uri="mongodb://localhost:27017", client=None):
        if client is None:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)

        self.client = client
        self.collection = client["pdf_search"]["documents"]
        self.collection.create_index("path", unique=True)

    def load(self):
        cache = {}

        for document in self.collection.find():
            cache[document["path"]] = {
                "signature": document["signature"],
                "text": document["text"],
            }

        return cache

    def save(self, cache):
        for path, document in cache.items():
            self.collection.replace_one(
                {"path": path},
                {
                    "path": path,
                    "signature": document["signature"],
                    "text": document["text"],
                },
                upsert=True,
            )

        self.collection.delete_many(
            {"path": {"$nin": list(cache)}}
        )
