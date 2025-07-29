from typing import Any, Iterator, Self

from qdrant_client import QdrantClient, models
from qdrant_client.conversions import common_types as types

from qdrant_odm.crud import ReadOptions, WriteOptions
from qdrant_odm.model import PointModel



class PointCRUD[T: PointModel]:
    def __init__(self, point_model_type: type[T], qdrant_client: QdrantClient):
        self._qdrant_client = qdrant_client
        self._point_model_type = point_model_type
        
    def get(self, id: Any, read_options: ReadOptions = ReadOptions()) -> T:
        """
        Get a point from Qdrant.

        Args:
            id (T): The id of the point to get.
            read_options (ReadOptions, optional): Read options. Defaults to ReadOptions().

        Returns:
            Self: The point.
        """
        record, *_ = self._qdrant_client.retrieve(
            self._point_model_type.__collection_name__, ids=[id], **read_options._asdict()
        )
        return self._point_model_type._from_record(record, set_persisted=True)
    
    def scroll(
        self,
        scroll_filter: types.Filter | None = None,
        limit: int = 10,
        order_by: types.OrderBy | None = None,
        read_options: ReadOptions = ReadOptions(),
    ) -> Iterator[list[T]]:
        """
        Scroll points from Qdrant.

        Args:
            scroll_filter (types.Filter | None, optional): Filter to apply. Defaults to None.
            limit (int, optional): Number of points to fetch per scroll. Defaults to 10.
            order_by (types.OrderBy | None, optional): Order by. Defaults to None.
            read_options (ReadOptions, optional): Read options. Defaults to ReadOptions().

        Yields:
            Iterator[list[T]]: Iterator of lists of points.
        """
        offset = None

        while True:
            records, offset = self._qdrant_client.scroll(
                self._point_model_type.__collection_name__,
                scroll_filter=scroll_filter,
                offset=offset,
                limit=limit,
                order_by=order_by,
                **read_options._asdict(),
            )
            yield [self._point_model_type._from_record(record, set_persisted=True) for record in records]

            if offset is None:
                break
    
    def insert_many(
        self,
        *points: T,
        write_options: WriteOptions = WriteOptions(),
    ) -> None:
        """
        Save the points to Qdrant.

        Args:
            write_options (WriteOptions, optional): Write options. Defaults to WriteOptions().
        """
        self._qdrant_client.upsert(
            self._point_model_type.__collection_name__,
            points=[
                models.PointStruct(
                    id=point.id, payload=point.payload(), vector=point.vectors()
                )
                for point in points
            ],
            **write_options._asdict(),
        )
        
    def delete_many(
        self,
        *points: T,
        write_options: WriteOptions = WriteOptions(),
    ) -> None:
        """
        Delete the points from Qdrant.

        Args:
            points_selector (Iterable[T]): Points selector.
            write_options (WriteOptions, optional): Write options. Defaults to WriteOptions().
        """
        self._qdrant_client.delete(
            self._point_model_type.__collection_name__,
            points_selector=models.PointIdsList(points=[point.id for point in points]),
            **write_options._asdict(),
        )

    def count(
        self,
        count_filter: types.Filter | None = None,
        exact: bool = True,
        shard_key_selector: types.ShardKeySelector | None = None,
        timeout: int | None = None,
    ) -> int:
        """
        Count points in collection.

        Args:
            count_filter (types.Filter | None, optional): Filter to apply. Defaults to None.
            exact (bool, optional): Whether to use exact count. Defaults to True.
            shard_key_selector (types.ShardKeySelector | None, optional): Shard key selector. Defaults to None.
            timeout (int | None, optional): Timeout. Defaults to None.

        Returns:
            int: Number of points
        """
        result = self._qdrant_client.count(
            self._point_model_type.__collection_name__,
            count_filter=count_filter,
            exact=exact,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return result.count

    def save(
        self,
        point: T,
        overwrite_vectors: bool = False,
        write_options: WriteOptions = WriteOptions(),
    ) -> None:
        """
        Save the point to Qdrant.

        Args:
            overwrite_vectors (bool, optional): Whether to overwrite the vectors if they already exist. Defaults to False.
            write_options (WriteOptions, optional): Write options. Defaults to WriteOptions().
        """
        write_kwargs = write_options._asdict()
        client = self._qdrant_client
        collection_name = self._point_model_type.__collection_name__
        payload = point.payload()

        if point._persisted:
            client.set_payload(
                collection_name,
                payload=payload,
                points=[point.id],
                **write_kwargs,
            )

            if overwrite_vectors:
                client.update_vectors(
                    collection_name,
                    points=[models.PointVectors(id=point.id, vector=point.vectors())],
                    **write_kwargs,
                )
        else:
            client.upsert(
                collection_name,
                points=[
                    models.PointStruct(
                        id=point.id, payload=payload, vector=point.vectors()
                    )
                ],
                **write_kwargs,
            )
            point._persisted = True

    def delete(self, id: Any, write_options: WriteOptions = WriteOptions()) -> None:
        """
        Delete the point from Qdrant.

        Args:
            write_options (WriteOptions, optional): Write options. Defaults to WriteOptions().
        """
        self._qdrant_client.delete(
            self._point_model_type.__collection_name__,
            points_selector=[id],
            **write_options._asdict(),
        )

    def prefetch(
        self,
        using: str,
        limit: int | None = None,
        score_threshold: float | None = None,
        prefetch_filter: types.Filter | None = None,
        params: types.SearchParams | None = None,
    ) -> Self:
        """
        Prefetch points from Qdrant.

        Args:
            using (str): The using vector to use.
            limit (int | None, optional): The limit of points to prefetch. Defaults to None.
            score_threshold (float | None, optional): The score threshold to use. Defaults to None.
            prefetch_filter (types.Filter | None, optional): The filter to use. Defaults to None.
            params (types.SearchParams | None, optional): The search params to use. Defaults to None.
        """

        # if not self._context_prefetch_is_on:
        #     raise ValueError(
        #         "Prefetch must be used in context manager. "
        #         "Use `with point.prefetch(...):`"
        #     )

        self._context_prefetch_is_on = False

        prefetch_query = models.Prefetch(
            query=self.id,
            using=using,
            limit=limit,
            score_threshold=score_threshold,
            filter=prefetch_filter,  # type: ignore
            prefetch=self._current_prefetch,
            params=params,  # type: ignore
        )

        self._current_prefetch = prefetch_query
        return self

if __name__ == "__main__":
    class CustomPoint(PointModel[int]):
        name: str = "custom"
        
    client = QdrantClient()
    
    crud = PointCRUD(CustomPoint, client)

    point = crud.get(12)
    
    