from typing import Any, Generic, TypeVar
from qdrant_client import QdrantClient, models
from qdrant_odm import PointModel, init_models, index

from qdrant_client.conversions import common_types as types

client = QdrantClient(prefer_grpc=True)

client.create_payload_index(
    collection_name="test",
    field_name="topic",
    field_type=models.PayloadSchemaType.TEXT,
)


class Chunk(PointModel[int]):
    topic: str = index.Text()
    keywords: list[str] = index.Keyword()
    is_active: bool = index.Bool()
    location: tuple[float, float] = index.Geo()
    nearest_chunks: list[tuple[float, float]] = index.MultiGeo()

    topic_vector: list[float] = index.Vector(100, models.Distance.COSINE)
    keywords_vectors: list[list[float]] = index.MultiVector(100, models.Distance.COSINE)
    keywords_vectors_sparse: tuple[list[int], list[float]] = index.SparseVector()

init_models(client, [Chunk])

chunk = Chunk(
    id=1,
    topic="test",
    keywords=["test1", "test2"],
    topic_vector=[1] * 100,
    keywords_vectors=[[1] * 100, [2] * 100],
    keywords_vectors_sparse=([0, 1], [1, 1]),
)

chunk.save()