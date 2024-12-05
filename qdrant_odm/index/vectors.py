from typing import Mapping, TypeAlias, TypedDict

from qdrant_client import models
from qdrant_client.conversions import common_types as types


DenseVectorType: TypeAlias = list[float]
DenseMultiVectorType: TypeAlias = list[DenseVectorType]
SparseVectorType: TypeAlias = tuple[list[int], list[float]]
BaseVectorType = DenseVectorType | DenseMultiVectorType | SparseVectorType


class BaseVectorIndex:
    _params: types.VectorParams | types.SparseVectorParams

    @property
    def params(self):
        return self._params


class Vector(DenseVectorType, BaseVectorIndex):
    """
    Params of single vector data storage
    """

    def __init__(
        self,
        size: int,
        distance: models.Distance,
        hnsw_config: models.HnswConfigDiff | None = None,
        quantization_config: models.QuantizationConfig | None = None,
        on_disk: bool | None = None,
        datatype: models.Datatype | None = None,
    ):
        self._params = models.VectorParams(
            size=size,
            distance=distance,
            hnsw_config=hnsw_config,
            quantization_config=quantization_config,
            on_disk=on_disk,
            datatype=datatype,
        )


class MultiVector(DenseMultiVectorType, BaseVectorIndex):
    """
    Params of multi vector data storage
    """

    def __init__(
        self,
        single_size: int,
        distance: models.Distance,
        multivector_config: models.MultiVectorConfig = models.MultiVectorConfig(
            comparator=models.MultiVectorComparator.MAX_SIM
        ),
        hnsw_config: models.HnswConfigDiff | None = None,
        quantization_config: models.QuantizationConfig | None = None,
        on_disk: bool | None = None,
        datatype: models.Datatype | None = None,
    ):
        self._params = models.VectorParams(
            size=single_size,
            distance=distance,
            hnsw_config=hnsw_config,
            quantization_config=quantization_config,
            on_disk=on_disk,
            datatype=datatype,
            multivector_config=multivector_config,
        )


class SparseVector(SparseVectorType, BaseVectorIndex):
    """
    Params of single sparse vector data storage
    """

    def __init__(
        self,
        index: models.SparseIndexParams | None = None,
        modifier: models.Modifier | None = None,
    ):
        self._params = models.SparseVectorParams(index=index, modifier=modifier)


# class VectorConfigs(TypedDict):
#     vectors_config: Mapping[str, types.VectorParams]
#     sparse_vectors_config: Mapping[str, types.SparseVectorParams]


# def build_vectors_config(cls: type[object]) -> VectorConfigs:
#     vectors_config, sparse_vectors_config = {}, {}

#     for field, type_ in cls.__annotations__.items():
#         if not hasattr(cls, field):
#             continue

#         msg = f"Vector field {field} must be of type {{}}. Got {type_}"
#         vector = getattr(cls, field)
#         if isinstance(vector, Vector):
#             assert type_ == DenseVectorType, msg.format(DenseVectorType)
#             vectors_config[field] = vector.params
#         elif isinstance(vector, MultiVector):
#             assert type_ == DenseMultiVectorType, msg.format(DenseMultiVectorType)
#             vectors_config[field] = vector.params
#         elif isinstance(vector, SparseVector):
#             assert type_ == SparseVectorType, msg.format(SparseVectorType)
#             sparse_vectors_config[field] = vector.params

#     return {
#         "vectors_config": vectors_config,
#         "sparse_vectors_config": sparse_vectors_config,
#     }
