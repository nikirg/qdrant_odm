from typing import Any, TypeAlias

from qdrant_client import models

KeywordType: TypeAlias = list[str]
IntegerType: TypeAlias = int
FloatType: TypeAlias = float
TextType: TypeAlias = str
BoolType: TypeAlias = bool
UuidType: TypeAlias = str
GeoType: TypeAlias = tuple[float, float]
MultiGeoType: TypeAlias = list[tuple[float, float]]
DatetimeType: TypeAlias = str


class BasePayloadIndex:
    _params: Any = None
    _key = None

    @property
    def params(self) -> Any:
        return self._params

    @property
    def key(self) -> str | None:
        return self._key


class Keyword(list[str], BasePayloadIndex):
    def __init__(
        self,
        is_tenant: bool | None = None,
        on_disk: bool | None = None,
        key: str | None = None,
    ):
        """
        Keyword index

        :param is_tenant: If true - used for tenant optimization. Default: false.
        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._params = models.KeywordIndexParams(
            type=models.KeywordIndexType.KEYWORD,
            is_tenant=is_tenant,
            on_disk=on_disk,
        )


class Integer(int, BasePayloadIndex):
    def __init__(
        self,
        lookup: bool | None = None,
        range: bool | None = None,
        is_principal: bool | None = None,
        on_disk: bool | None = None,
        key: str | None = None,
    ):
        """
        Integer index

        :param lookup: If true - support direct lookups.
        :param range: If true - support ranges filters.
        :param is_principal: If true - use this key to organize storage of the collection data. This option assumes that this key will be used in majority of filtered requests.
        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.IntegerIndexParams(
            type=models.IntegerIndexType.INTEGER,
            lookup=lookup,
            range=range,
            is_principal=is_principal,
            on_disk=on_disk,
        )


class Float(float, BasePayloadIndex):
    def __init__(
        self,
        is_principal: bool | None = None,
        on_disk: bool | None = None,
        key: str | None = None,
    ):
        """
        Float index

        :param is_principal: If true - use this key to organize storage of the collection data. This option assumes that this key will be used in majority of filtered requests.
        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.FloatIndexParams(
            type=models.FloatIndexType.FLOAT,
            is_principal=is_principal,
            on_disk=on_disk,
        )


def Bool(key: str | None = None) -> Any:  # type: ignore
    return key, models.BoolIndexParams(
        type=models.BoolIndexType.BOOL,
    )


class Geo(tuple[float, float], BasePayloadIndex):
    def __init__(self, on_disk: bool | None = None, key: str | None = None):
        """
        Geo index

        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.GeoIndexParams(
            type=models.GeoIndexType.GEO,
            on_disk=on_disk,
        )


class MultiGeo(list[tuple[float, float]], BasePayloadIndex):
    def __init__(self, on_disk: bool | None = None, key: str | None = None):
        """
        Multiple geo index

        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.GeoIndexParams(
            type=models.GeoIndexType.GEO,
            on_disk=on_disk,
        )


class Datetime(int, BasePayloadIndex):
    def __init__(
        self,
        is_principal: bool | None = None,
        on_disk: bool | None = None,
        key: str | None = None,
    ):
        """
        Datetime index

        :param is_principal: If true - use this key to organize storage of the collection data. This option assumes that this key will be used in majority of filtered requests.
        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.DatetimeIndexParams(
            type=models.DatetimeIndexType.DATETIME,
            is_principal=is_principal,
            on_disk=on_disk,
        )


class Text(str, BasePayloadIndex):
    def __init__(
        self,
        tokenizer: models.TokenizerType = models.TokenizerType.WORD,
        min_token_len: int | None = None,
        max_token_len: int | None = None,
        lowercase: bool | None = None,
        on_disk: bool | None = None,
        key: str | None = None,
    ):
        """
        Full text index

        :param tokenizer: Tokenizer type.
        :param min_token_len: Minimum characters to be tokenized.
        :param max_token_len: Maximum characters to be tokenized.
        :param lowercase: If true, lowercase all tokens. Default: true.
        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.TextIndexParams(
            type=models.TextIndexType.TEXT,
            tokenizer=tokenizer,
            min_token_len=min_token_len,
            max_token_len=max_token_len,
            lowercase=lowercase,
            on_disk=on_disk,
        )


class Uuid(str, BasePayloadIndex):
    def __init__(
        self,
        is_tenant: bool | None = None,
        on_disk: bool | None = None,
        key: str | None = None,
    ):
        """
        Uuid index

        :param is_tenant: If true - used for tenant optimization. Default: false.
        :param on_disk: If true, store the index on disk. Default: false.
        :param key: Key for nested field. You can use dot notation to specify the path to the nested field.
        """
        self._key = key
        self._index_params = models.UuidIndexParams(
            type=models.UuidIndexType.UUID,
            is_tenant=is_tenant,
            on_disk=on_disk,
        )
