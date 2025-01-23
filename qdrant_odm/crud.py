from typing import Iterable, Iterator, NamedTuple, Self, Sequence
from types import TracebackType

from qdrant_client import models
from qdrant_client.conversions import common_types as types

from .model import PointModel, T


class ReadOptions(NamedTuple):
    with_vectors: bool | Sequence[str] = False
    consistency: types.ReadConsistency | None = None
    shard_key_selector: types.ShardKeySelector | None = None
    timeout: int | None = None


class WriteOptions(NamedTuple):
    wait: bool = True
    ordering: types.WriteOrdering | None = None
    shard_key_selector: types.ShardKeySelector | None = None


class CRUDPoint(PointModel[T]):
    @classmethod
    def get(
        cls,
        id: T,
        read_options: ReadOptions = ReadOptions(),
    ) -> Self:
        """
        Get a point from Qdrant.

        Args:
            id (T): The id of the point to get.
            read_options (ReadOptions, optional): Read options. Defaults to ReadOptions().

        Returns:
            Self: The point.
        """
        record, *_ = cls.__client__.retrieve(
            cls.__collection_name__, ids=[id], **read_options._asdict()
        )
        return cls._from_record(record, set_persisted=True)

    @classmethod
    def scroll(
        cls,
        scroll_filter: types.Filter | None = None,
        limit: int = 10,
        order_by: types.OrderBy | None = None,
        read_options: ReadOptions = ReadOptions(),
    ) -> Iterator[list[Self]]:
        """
        Scroll points from Qdrant.

        Args:
            scroll_filter (types.Filter | None, optional): Filter to apply. Defaults to None.
            limit (int, optional): Number of points to fetch per scroll. Defaults to 10.
            order_by (types.OrderBy | None, optional): Order by. Defaults to None.
            read_options (ReadOptions, optional): Read options. Defaults to ReadOptions().

        Yields:
            Iterator[list[Self]]: Iterator of lists of points.
        """
        offset = None

        while True:
            records, offset = cls.__client__.scroll(
                cls.__collection_name__,
                scroll_filter=scroll_filter,
                offset=offset,
                limit=limit,
                order_by=order_by,
                **read_options._asdict(),
            )
            yield [cls._from_record(record, set_persisted=True) for record in records]

            if offset is None:
                break

    @classmethod
    def insert_many(
        cls,
        *points: Self,
        write_options: WriteOptions = WriteOptions(),
    ) -> None:
        """
        Save the points to Qdrant.

        Args:
            write_options (WriteOptions, optional): Write options. Defaults to WriteOptions().
        """
        cls.__client__.upsert(
            cls.__collection_name__,
            points=[
                models.PointStruct(
                    id=point.id, payload=point.payload(), vector=point.vectors()
                )
                for point in points
            ],
            **write_options._asdict(),
        )

    @classmethod
    def count(
        cls,
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
        result = cls.__client__.count(
            cls.__collection_name__,
            count_filter=count_filter,
            exact=exact,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return result.count

    def save(
        self,
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
        client = self.__client__
        collection_name = self.__collection_name__
        payload = self.payload()

        if self._persisted:
            client.set_payload(
                collection_name,
                payload=payload,
                points=[self.id],
                **write_kwargs,
            )

            if overwrite_vectors:
                client.update_vectors(
                    collection_name,
                    points=[models.PointVectors(id=self.id, vector=self.vectors())],
                    **write_kwargs,
                )
        else:
            client.upsert(
                collection_name,
                points=[
                    models.PointStruct(
                        id=self.id, payload=payload, vector=self.vectors()
                    )
                ],
                **write_kwargs,
            )
            self._persisted = True

    def delete(self, write_options: WriteOptions = WriteOptions()) -> None:
        """
        Delete the point from Qdrant.

        Args:
            write_options (WriteOptions, optional): Write options. Defaults to WriteOptions().
        """
        if not self._persisted:
            raise ValueError(
                "Cannot delete non-persisted point. You need to save it first."
            )

        self.__client__.delete(
            self.__collection_name__,
            points_selector=[self.id],
            **write_options._asdict(),
        )

    def sync(self, read_options: ReadOptions = ReadOptions()) -> None:
        """
        Syncronize the object with Qdrant record.

        Args:
            read_options (ReadOptions, optional): Read options. Defaults to ReadOptions().
        """
        persisted_point = self.get(self.id, read_options)
        for field in self.fields:
            if persisted_value := getattr(persisted_point, field, None):
                setattr(self, field, persisted_value)
        self._persisted = True

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

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type, exc_value: Exception, traceback: TracebackType):
        if current_prefetch := self._current_prefetch:
            self._current_prefetch = current_prefetch.prefetch  # type: ignore

    def neighbors(
        self,
        using: str,
        limit: int = 10,
        score_threshold: float | None = None,
        query_filter: types.Filter | None = None,
        read_options: ReadOptions = ReadOptions(),
        search_params: types.SearchParams | None = None,
    ) -> list[tuple[Self, float]]:
        """
        Get neighbors for the point.

        Args:
            using (str): which vector field to use
            limit (int, optional): Limit. Defaults to 10.
            score_threshold (float | None, optional): Score threshold. Defaults to None.
            query_filter (types.Filter | None, optional): Query filter. Defaults to None.
            prefetch (models.Prefetch | None, optional): Prefetch. Defaults to None.
            read_options (ReadOptions, optional): Read options. Defaults to ReadOptions().
            search_params (SearchParams, optional): Search params.

        Yields:
            Iterable[tuple[Self, float]]: Iterator of neighbors.
        """

        if not self._persisted:
            raise ValueError(
                "Cannot get neighbors for non-persisted point. You need to save it first."
            )

        response = self.__client__.query_points(
            self.__collection_name__,
            query=self.id,
            using=using,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            prefetch=self._current_prefetch,
            search_params=search_params,
            **read_options._asdict(),
        )

        return [
            (self._from_record(record, set_persisted=True), record.score)
            for record in response.points
        ]
