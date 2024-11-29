from typing import ClassVar, Generic, TypeVar
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.conversions import common_types as types

from .dataclass import DataClass
from .vectors import build_vectors_config


class CollectionConfig(DataClass):
    collection_name: str | None = None
    shard_number: int | None = None
    sharding_method: types.ShardingMethod | None = None
    replication_factor: int | None = None
    write_consistency_factor: int | None = None
    on_disk_payload: bool | None = None
    hnsw_config: types.HnswConfigDiff | None = None
    optimizers_config: types.OptimizersConfigDiff | None = None
    wal_config: types.WalConfigDiff | None = None
    quantization_config: types.QuantizationConfig | None = None
    init_from: types.InitFrom | None = None
    timeout: int | None = None


T = TypeVar("T", bound=int | UUID)


class Point(DataClass, Generic[T]):
    collection_config: ClassVar[CollectionConfig]

    id: T

    @classmethod
    def init_collection(cls, client: QdrantClient):
        if cls.collection_config:
            collection_name = cls.collection_config.collection_name or cls.__name__
            config = cls.collection_config.to_dict(exclude={"collection_name"})
        else:
            collection_name = cls.__name__
            config = {}

        config |= build_vectors_config(cls)

        if client.collection_exists(collection_name):
            client.update_collection(
                collection_name=collection_name,
                **config,
            )
        else:
            client.create_collection(
                collection_name=collection_name,
                **config,
            )


if __name__ == "__main__":
    from qdrant_client import models, QdrantClient
    from qdrant_odm.vectors import Vector, MultiVector, SparseVector

    client = QdrantClient()

    class Chunk(Point[UUID]):
        topic: str
        keywords: list[str] | None = None

        topic_vector: list[float] = Vector(size=128, distance=models.Distance.COSINE)
        keywords_vectors: list[list[float]] | None = MultiVector(
            single_size=128, distance=models.Distance.COSINE
        )
        keywords_hashmap: tuple[list[int], list[float]] = SparseVector()

    Chunk(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        topic="test",
        topic_vector=[0.1, 0.2, 0.3],
    )
