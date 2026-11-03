"""
MongoDB Document Client with Local JSON-backed Fallback.
Stores flexible raw event payloads, clickstream logs, and dead-letter events.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class MongoClientWrapper:
    def __init__(self, host: str = "localhost", port: int = 27017, db_name: str = "ecommerce_events"):
        self.host = os.getenv("MONGO_HOST", host)
        self.port = int(os.getenv("MONGO_PORT", port))
        self.db_name = os.getenv("MONGO_DB", db_name)
        self.user = os.getenv("MONGO_USER", "mongoadmin")
        self.password = os.getenv("MONGO_PASSWORD", "mongopassword")

        self.is_live_mongo = False
        self.local_store_path = os.path.abspath("data/mongo_storage")
        os.makedirs(self.local_store_path, exist_ok=True)
        self._init_connection()

    def _init_connection(self):
        try:
            from pymongo import MongoClient
            uri = f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/"
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.is_live_mongo = True
            print(">> Connected to live MongoDB service.")
        except Exception:
            self.is_live_mongo = False
            self.client = None
            self.db = None

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Inserts a single JSON document."""
        if self.is_live_mongo:
            res = self.db[collection_name].insert_one(document)
            return str(res.inserted_id)
        
        # Local fallback
        coll_file = os.path.join(self.local_store_path, f"{collection_name}.jsonl")
        doc_copy = document.copy()
        if "_id" not in doc_copy:
            doc_copy["_id"] = f"doc_{datetime.now(timezone.utc).timestamp()}_{os.urandom(4).hex()}"
        
        with open(coll_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(doc_copy, default=str) + "\n")
        return doc_copy["_id"]

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Inserts multiple JSON documents in bulk."""
        if not documents:
            return []

        if self.is_live_mongo:
            res = self.db[collection_name].insert_many(documents)
            return [str(_id) for _id in res.inserted_ids]

        coll_file = os.path.join(self.local_store_path, f"{collection_name}.jsonl")
        ids = []
        with open(coll_file, "a", encoding="utf-8") as f:
            for doc in documents:
                doc_copy = doc.copy()
                doc_id = f"doc_{os.urandom(6).hex()}"
                doc_copy["_id"] = doc_id
                f.write(json.dumps(doc_copy, default=str) + "\n")
                ids.append(doc_id)
        return ids

    def find(self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Queries documents matching filters."""
        if self.is_live_mongo:
            cursor = self.db[collection_name].find(filter_dict or {}).limit(limit)
            return list(cursor)

        coll_file = os.path.join(self.local_store_path, f"{collection_name}.jsonl")
        if not os.path.exists(coll_file):
            return []

        results = []
        with open(coll_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                doc = json.loads(line)
                match = True
                if filter_dict:
                    for k, v in filter_dict.items():
                        if doc.get(k) != v:
                            match = False
                            break
                if match:
                    results.append(doc)
                    if len(results) >= limit:
                        break
        return results

    def count(self, collection_name: str) -> int:
        """Returns total document count in collection."""
        if self.is_live_mongo:
            return self.db[collection_name].count_documents({})
        
        coll_file = os.path.join(self.local_store_path, f"{collection_name}.jsonl")
        if not os.path.exists(coll_file):
            return 0
        with open(coll_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

