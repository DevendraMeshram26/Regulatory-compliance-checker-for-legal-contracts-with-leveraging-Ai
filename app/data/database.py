import chromadb
import pandas as pd

class ChromaDBManager:
    def __init__(self):
        self.client = chromadb.Client()
        
    def initialize_collection(self):
        try:
            collection_name = "DatasetEx"
            try:
                collection = self.client.get_collection(name=collection_name)
                print(f"Collection {collection_name} already exists")
            except Exception:
                print(f"Creating new collection: {collection_name}")
                collection = self.client.create_collection(name=collection_name)
                self._load_initial_data(collection)
            return collection
        except Exception as e:
            print(f"Error initializing ChromaDB: {str(e)}")
            return None
            
    def _load_initial_data(self, collection):
        # ... existing CSV loading logic ...
        pass 