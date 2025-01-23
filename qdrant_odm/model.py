from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Mapping,
    NamedTuple,
    Self,
    TypeVar,
    TypedDict,
)

from loguru import logger
from pydantic import BaseModel
from qdrant_client import QdrantClient, models as qmodels
from qdrant_client.conversions import common_types as types

from .dataclass import DataClass
from .index.vectors import (
    SparseVectorType,
    BaseVectorIndex,
    DenseVectorType,
    DenseMultiVectorType,
    SparseVectorType,
    SparseVector,
    Vector,
    MultiVector,
)
from .index.payload import (
    BasePayloadIndex,
    Keyword,
    Integer,
    Text,
    Bool,
    Uuid,
    Geo,
    MultiGeo,
    Float,
    Datetime,
    KeywordType,
    IntegerType,
    FloatType,
    TextType,
    BoolType,
    UuidType,
    GeoType,
    MultiGeoType,
    DatetimeType,
)

T = TypeVar("T", bound=int | str)


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


class VectorConfigs(TypedDict):
    vectors_config: Mapping[str, types.VectorParams]
    sparse_vectors_config: Mapping[str, types.SparseVectorParams]


class PayloadParams(NamedTuple):
    params: BaseModel
    key: str | None


class IndexConfig(NamedTuple):
    vectors: VectorConfigs
    payloads: Mapping[str, PayloadParams]


class PointModel(DataClass, Generic[T]):
    __client__: ClassVar[QdrantClient]
    __collection_name__: ClassVar[str]
    __non_payload_fields__: ClassVar[set[str]] = {"id"}

    collection_config: ClassVar[CollectionConfig] = CollectionConfig()

    id: T

    @classmethod
    def _build_index_config(cls) -> VectorConfigs:
        vectors_config, sparse_vectors_config = {}, {}
        payload_indicies = {}

        for field, type_ in cls.__annotations__.items():
            if not hasattr(cls, field):
                continue

            # value = getattr(cls, field)

            # if isinstance(value, BasePayloadIndex):
            #     pass
            #     # msg = f"Payload field {field} must be of type {{}}. Got {type_}"

            #     # if isinstance(value, Keyword):
            #     #     assert type_ == KeywordType, msg.format(KeywordType)
            #     #     payload_indicies[field] = value.params
            #     # elif isinstance(value, Integer):
            #     #     assert type_ == IntegerType, msg.format(IntegerType)
            #     #     payload_indicies[field] = value.params
            #     # elif isinstance(value, Text):
            #     #     assert type_ == TextType, msg.format(TextType)
            #     #     payload_indicies[field] = value.params

            #     # elif isinstance(value, Uuid):
            #     #     assert type_ == UuidType, msg.format(UuidType)
            #     #     payload_indicies[field] = value.params
            #     # elif isinstance(value, Geo):
            #     #     assert type_ == GeoType, msg.format(GeoType)
            #     #     payload_indicies[field] = value.params
            #     # elif isinstance(value, MultiGeo):
            #     #     assert type_ == MultiGeoType, msg.format(MultiGeoType)
            #     #     payload_indicies[field] = value.params
            #     # elif isinstance(value, Float):
            #     #     assert type_ == FloatType, msg.format(FloatType)
            #     #     payload_indicies[field] = value.params

            # elif isinstance(value, Callable) and value.__name__ == "Bool":
            #     msg = f"Payload field {field} must be of type {{}}. Got {type_}"
            #     assert type_ == BoolType, msg.format(BoolType)
            #     payload_indicies[field] = value

            # elif isinstance(cls, BaseVectorIndex):
            msg = f"Vector field {field} must be of type {{}}. Got {type_}"
            value = getattr(cls, field)

            if isinstance(value, Vector):
                assert type_ == DenseVectorType, msg.format(DenseVectorType)
                vectors_config[field] = value.params
            elif isinstance(value, MultiVector):
                assert type_ == DenseMultiVectorType, msg.format(DenseMultiVectorType)
                vectors_config[field] = value.params
            elif isinstance(value, SparseVector):
                assert type_ == SparseVectorType, msg.format(SparseVectorType)
                sparse_vectors_config[field] = value.params

        return {
            "vectors_config": vectors_config,
            "sparse_vectors_config": sparse_vectors_config,
        }

    @classmethod
    def init_collection(cls, client: QdrantClient):
        cls.__client__ = client

        if cls.collection_config.collection_name is None:
            cls.collection_config.collection_name = cls.__name__

        cls.__collection_name__ = cls.collection_config.collection_name

        index_config = cls._build_index_config()

        cls.__non_payload_fields__.update(index_config["vectors_config"])
        cls.__non_payload_fields__.update(index_config["sparse_vectors_config"])

        if client.collection_exists(cls.collection_config.collection_name):
            pass
            # logger.info(
            #     "Collection already exists, if you want to update it use update_collection manually",
            # )
        else:
            index_config |= cls.collection_config.to_dict()
            client.create_collection(**index_config)  # type: ignore

    @classmethod
    def _from_record(
        cls, record: types.Record | types.ScoredPoint, set_persisted: bool = False
    ) -> Self:
        point = cls(id=record.id, **record.payload or {}, **record.vector or {})  # type: ignore
        point._persisted = set_persisted
        return point

    def __post_init__(self):
        self._persisted = False
        self._current_prefetch: types.Prefetch | None = None
        self._context_prefetch_is_on = False

    @property
    def persisted(self) -> bool:
        return self._persisted

    def payload(self) -> dict[str, Any]:
        return self.to_dict(exclude=self.__non_payload_fields__)

    def vectors(self) -> dict[str, types.Vector]:
        result = {}

        for field in self.__non_payload_fields__:
            if field == "id":
                continue

            if vector := getattr(self, field, None):
                if type(vector) is SparseVectorType:
                    result[field] = qmodels.SparseVector(
                        indices=vector[0], values=vector[1]
                    )
                else:
                    result[field] = vector

        return result


def init_models(client: QdrantClient, models: list[type[PointModel[T]]]):
    for model in models:
        model.init_collection(client)
