# Copyright (c) 2023-2024 Codelet Team (pyxfluff / iiPythonx)
# Repurposed bc it's running on the same VM

# Modules
import platform
from typing import Any, List, Dict

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Main database class
class Database(object):
    def __init__(self) -> None:

        # Reference tables
        for db_item in ["error_refs", "apps", "proxy_cache", "api_keys", "places", "abuse_logs"]:
            setattr(self, db_item.upper(), db_item)

        # Connect to Mongo
        client = MongoClient("zen" in platform.release() and "mongodb://mail.iipython.dev:27017" or "mongodb://127.0.0.1:27017", serverSelectionTimeoutMS = 3000)

        self.db = client["administer"]  # administer database to hopefully not mess with codelet dev

        # Test connection
        try:
            client.admin.command("ping")

        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB within the required timeframe! Is Mongo running? Aborting startup...")
            raise e

    def set(self, key: str | int, value: Any, db: str) -> None:
        assert isinstance(key, (str, int)), "key must be a string (integers accepted)!"
        assert isinstance(db, str), "db must be a string!"

        if db == self.APPS:
            key = str(key)

        db = self.db[db]

        # Fetch active document
        internal_document = {"administer_id": str(key)}
        active_document = db.find_one(internal_document)
        if active_document is not None:
            return db.update_one(
                {"_id": active_document["_id"]},
                {"$set": {"data": value}}
            )

        return db.insert_one(internal_document | {"data": value})

    def set_batch(self, items: Dict[str | int, dict], db: str) -> None:
        assert isinstance(items, dict), "items must be a dict!"
        assert isinstance(db, str), "db must be a string!"

        for k, v in items.items():
            self.set(k, v, db)

    def get(self, key: str | int, db: str) -> dict | None:
        assert isinstance(key, (str, int)), "key must be a string (integers accepted)"
        assert isinstance(db, str), "db must be an attr of db"

        document = self.db[db].find_one({"administer_id": str(key)})
        return document and document["data"]

    def find(self, identifier: dict, db: str) -> str | None:
        assert isinstance(identifier, dict), "identifier must be a dict!"
        assert isinstance(db, str), "db must be a string!"

        document = self.db[db].find_one({f"data.{k}": v for k, v in identifier.items()})
        return document and document["administer_id"]

    def delete(self, key: str | int, db: str) -> None:
        assert isinstance(key, (str, int)), "key must be a string or integer!"

        self.db[db].delete_one({"administer_id": str(key)})

    def bulk_delete(self, keys: List[str | int], db: str) -> None:
        assert isinstance(keys, list), "keys must be a list! (try using db.delete())"

        self.db[db].delete_many({"administer_id": {"$in": keys}})
    
    def get_all(self, db: str) -> dict:
       return list(self.db[db].find())
    
    def get_all_paged(self, db: str, limit: int, page: int) -> List[dict]:
        return [d["data"] for d in list(self.db[db].aggregate([{"$skip": limit * (page - 1)}, {"$limit": limit}]))]

    # Wrappers for raw MongoDB operations
    def raw_insert(self, item: dict, db: str) -> None:
        self.db[db].insert_one(item)

    def raw_find(self, identifier: dict, db: str) -> dict:
        return self.db[db].find_one(identifier)
    
    def raw_del(self, identifier: dict, db: str) -> dict:
        return self.db[db].delete_one(identifier)
    
    def raw_purge(self, identifier: dict, db: str) -> dict:
        return self.db[db].delete_many(identifier)


    def raw_find_all(self, identifier: dict, db: str) -> List[dict]:
        return self.db[db].find(identifier)

# Initialize db
db = Database() 