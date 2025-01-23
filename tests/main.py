from qdrant_client import QdrantClient, models
from qdrant_odm import PointModel, init_models, index

client = QdrantClient(prefer_grpc=True)


class Chunk(PointModel[int]):
    # topic: str = index.Text()
    # keywords: list[str] = index.Keyword()
    # is_active: bool = index.Bool()
    # location: tuple[float, float] = index.Geo()
    # nearest_chunks: list[tuple[float, float]] = index.MultiGeo()

    topic_vector: list[float] = index.Vector(100, models.Distance.COSINE)
    title_vector: list[float] = index.Vector(100, models.Distance.COSINE)
    description_vector: list[float] = index.Vector(100, models.Distance.COSINE)
    # keywords_vectors: list[list[float]] = index.MultiVector(100, models.Distance.COSINE)
    # keywords_vectors_sparse: tuple[list[int], list[float]] = index.SparseVector()


init_models(client, [Chunk])

chunk = Chunk(
    id=2,
    # topic="test",
    # keywords=["test1", "test2"],
    topic_vector=[1] * 100,
    title_vector=[1] * 100,
    description_vector=[1] * 100,
    # keywords_vectors=[[1] * 100, [2] * 100],
    # keywords_vectors_sparse=([0, 1], [1, 1]),
)

chunk.save()

with chunk.prefetch("topic_vector"):
    with chunk.prefetch("title_vector"):
        neighbors = chunk.neighbors(using="description_vector")
        print(neighbors)
