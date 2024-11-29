from .point import Point

from qdrant_client import QdrantClient

client = QdrantClient()

client.upsert(
    collection_name="test",
    points=[Point(id=1, vector=[0.1, 0.2, 0.3])],    
)

class CRUDPoint(Point):
    def save(self):
        pass