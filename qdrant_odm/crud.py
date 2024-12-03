from typing import Iterator, NamedTuple, Self, Sequence

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

        if self._persisted:
            client.set_payload(
                collection_name,
                payload=self.payload(),
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
                        id=self.id, payload=self.payload(), vector=self.vectors()
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
        """
        persisted_point = self.get(self.id, read_options)
        for field in self.fields:
            if persisted_value := getattr(persisted_point, field, None):
                setattr(self, field, persisted_value)
        self._persisted = True

    # def neighbors(
    #     self,
    #     using: set[str] | None = None,
    #     limit: int = 10,
    #     score_threshold: float | None = None,
    #     query_filter: types.Filter | None = None,
    #     read_options: ReadOptions = ReadOptions(),
    # ) -> list[Self]:
    #     if not self._persisted:
    #         raise ValueError(
    #             "Cannot get neighbors for non-persisted point. You need to save it first."
    #         )
    #     self.__client__.query_points(self.__collection_name__, query=self.id)
    