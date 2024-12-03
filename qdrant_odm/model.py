from typing import Any, ClassVar, Generic, Self, TypeVar

from qdrant_client import QdrantClient, models as qmodels
from qdrant_client.conversions import common_types as types
from loguru import logger

from .dataclass import DataClass
from .index.vectors import SparseVectorType, build_vectors_config


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


T = TypeVar("T", bound=int | str)

_exclude_on_update = {
    "shard_number",
    "sharding_method",
    "replication_factor",
    "write_consistency_factor",
    "on_disk_payload",
    "wal_config",
    "init_from",
}


class PointModel(DataClass, Generic[T]):
    __client__: ClassVar[QdrantClient]
    __collection_name__: ClassVar[str]
    __non_payload_fields__: ClassVar[set[str]] = {"id"}

    collection_config: ClassVar[CollectionConfig] = CollectionConfig()

    id: T

    @classmethod
    def init_collection(cls, client: QdrantClient):
        cls.__client__ = client

        if cls.collection_config.collection_name is None:
            cls.collection_config.collection_name = cls.__name__

        cls.__collection_name__ = cls.collection_config.collection_name

        config = build_vectors_config(cls)

        cls.__non_payload_fields__.update(config["vectors_config"])
        cls.__non_payload_fields__.update(config["sparse_vectors_config"])

        if client.collection_exists(cls.collection_config.collection_name):
            logger.info(
                "Collection already exists, if you want to update it use update_collection manually",
            )
            # info = client.get_collection(cls.collection_config.collection_name)
            # config |= cls.collection_config.to_dict(exclude=_exclude_on_update)
            # client.update_collection(**config)  # type: ignore
        else:
            config |= cls.collection_config.to_dict()
            client.create_collection(**config)  # type: ignore

    @classmethod
    def _from_record(cls, record: types.Record, set_persisted: bool = False) -> Self:
        point = cls(id=record.id, **record.payload or {}, **record.vector or {})  # type: ignore
        point._persisted = set_persisted
        return point

    def payload(self) -> dict[str, Any]:
        return self.to_dict(exclude=self.__non_payload_fields__)

    def vectors(self) -> dict[str, types.Vector]:
        result = {}

        for field in self.__non_payload_fields__:
            if field == "id":
                continue

            if vector := getattr(self, field):
                if type(vector) is SparseVectorType:
                    result[field] = qmodels.SparseVector(
                        indices=vector[0], values=vector[1]
                    )
                else:
                    result[field] = vector

        return result

    def __post_init__(self):
        self._persisted = False

    @property
    def persisted(self) -> bool:
        return self._persisted


def init_models(client: QdrantClient, models: list[type[PointModel[T]]]):
    for model in models:
        model.init_collection(client)
