class Keyword(list[str]):
    __field_schema__ = models.PayloadSchemaType.KEYWORD

    def __init__(self, is_tenant: bool | None = None, on_disk: bool | None = None):
        """
        Keyword index

        :param is_tenant: If true - used for tenant optimization. Default: false.
        :param on_disk: If true, store the index on disk. Default: false.
        """
        models.KeywordIndexParams(
            type=models.KeywordIndexType.KEYWORD,
            is_tenant=is_tenant,
            on_disk=on_disk,
        )


class Integer(int):
    __field_schema__ = models.PayloadSchemaType.INTEGER

    def __init__(
        self,
        lookup: bool | None = None,
        range: bool | None = None,
        is_principal: bool | None = None,
        on_disk: bool | None = None,
    ):
        """
        Integer index

        :param lookup: If true - support direct lookups.
        :param range: If true - support ranges filters.
        :param is_principal: If true - use this key to organize storage of the collection data. This option assumes that this key will be used in majority of filtered requests.
        :param on_disk: If true, store the index on disk. Default: false.
        """
        models.IntegerIndexParams(
            type=models.IntegerIndexType.INTEGER,
            lookup=lookup,
            range=range,
            is_principal=is_principal,
            on_disk=on_disk,
        )


class Float(float):
    __field_schema__ = models.PayloadSchemaType.FLOAT

    def __init__(
        self,
        is_principal: bool | None = None,
        on_disk: bool | None = None,
    ):
        """
        Float index

        :param is_principal: If true - use this key to organize storage of the collection data. This option assumes that this key will be used in majority of filtered requests.
        :param on_disk: If true, store the index on disk. Default: false.

        """
        models.FloatIndexParams(
            type=models.FloatIndexType.FLOAT,
            is_principal=is_principal,
            on_disk=on_disk,
        )


def Bool() -> Any:  # type: ignore
    field_schema = models.PayloadSchemaType.BOOL

    models.BoolIndexParams(
        type=models.BoolIndexType.BOOL,
    )
    return field_schema


class Geo(tuple[float, float]):
    __field_schema__ = models.PayloadSchemaType.GEO

    def __init__(self, on_disk: bool | None = None):
        """
        Geo index

        :param on_disk: If true, store the index on disk. Default: false.
        """
        models.GeoIndexParams(
            type=models.GeoIndexType.GEO,
            on_disk=on_disk,
        )


class MultiGeo(list[tuple[float, float]]):
    __field_schema__ = models.PayloadSchemaType.GEO

    def __init__(self, on_disk: bool | None = None):
        """
        Geo index

        :param on_disk: If true, store the index on disk. Default: false.
        """
        models.GeoIndexParams(
            type=models.GeoIndexType.GEO,
            on_disk=on_disk,
        )


class Datetime(int):
    __field_schema__ = models.PayloadSchemaType.DATETIME

    def __init__(self, is_principal: bool | None = None, on_disk: bool | None = None):
        """
        Datetime index

        :param is_principal: If true - use this key to organize storage of the collection data. This option assumes that this key will be used in majority of filtered requests.
        :param on_disk: If true, store the index on disk. Default: false.
        """
        models.DatetimeIndexParams(
            type=models.DatetimeIndexType.DATETIME,
            is_principal=is_principal,
            on_disk=on_disk,
        )


class Text(str):
    __field_schema__ = None

    def __init__(
        self,
        tokenizer: models.TokenizerType = models.TokenizerType.WORD,
        min_token_len: int | None = None,
        max_token_len: int | None = None,
        lowercase: bool | None = None,
        on_disk: bool | None = None,
    ):
        """
        Full text index

        :param tokenizer: Tokenizer type.
        :param min_token_len: Minimum characters to be tokenized.
        :param max_token_len: Maximum characters to be tokenized.
        :param lowercase: If true, lowercase all tokens. Default: true.
        :param on_disk: If true, store the index on disk. Default: false.
        """
        self.__field_schema__ = models.TextIndexParams(
            type=models.TextIndexType.TEXT,
            tokenizer=tokenizer,
            min_token_len=min_token_len,
            max_token_len=max_token_len,
            lowercase=lowercase,
            on_disk=on_disk,
        )

    @property
    def field_schema(self) -> models.TextIndexParams | None:
        return self.__field_schema__


class Uuid(str):
    __field_schema__ = models.PayloadSchemaType.UUID

    def __init__(self, is_tenant: bool | None = None, on_disk: bool | None = None):
        """
        Uuid index

        :param is_tenant: If true - used for tenant optimization. Default: false.
        :param on_disk: If true, store the index on disk. Default: false.
        """
        models.UuidIndexParams(
            type=models.UuidIndexType.UUID,
            is_tenant=is_tenant,
            on_disk=on_disk,
        )
