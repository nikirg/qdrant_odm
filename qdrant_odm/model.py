from typing import Any, ClassVar, Generic, Self, TypeVar

from qdrant_client import QdrantClient, models as qmodels
from qdrant_client.conversions import common_types as types

from .dataclass import DataClass
from .vectors import SparseVectorType, build_vectors_config


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


class PointModel(DataClass, Generic[T]):
    __client__: ClassVar[QdrantClient]
    __collection_name__: ClassVar[str]
    __non_payload_fields__: ClassVar[set[str]] = {"id"}

    collection_config: ClassVar[CollectionConfig]

    id: T

    @classmethod
    def init_collection(cls, client: QdrantClient):
        cls.__client__ = client

        config = cls.collection_config or CollectionConfig()

        if config.collection_name is None:
            config.collection_name = cls.__name__

        cls.__collection_name__ = config.collection_name

        vectors_config = build_vectors_config(cls)

        cls.__non_payload_fields__.union(
            vectors_config["vectors_config"], vectors_config["sparse_vectors_config"]
        )

        config_dict: dict[str, Any] = config.to_dict() | vectors_config

        if client.collection_exists(config.collection_name):
            client.update_collection(**config_dict)
        else:
            client.create_collection(**config_dict)

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

            vector = getattr(self, field)
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


def init_models(client: QdrantClient, models: list[type[PointModel]]):
    for model in models:
        model.init_collection(client)
