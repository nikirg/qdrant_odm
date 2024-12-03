from typing import Any, ClassVar, dataclass_transform


class Serializable:
    def __init__(self, **kwargs: Any):
        for field in self.fields:
            setattr(self, field, kwargs.get(field))

    @property
    def fields(self) -> dict[str, Any]:
        parent_annotations = {}
        parents_stack = [self.__class__.__bases__]

        while parents_stack:
            for base in parents_stack.pop():
                if hasattr(base, "__annotations__"):
                    for field, type_ in base.__annotations__.items():
                        if getattr(type_, "__origin__", None) is not ClassVar:
                            parent_annotations[field] = type_
                if base.__bases__:
                    parents_stack.append(base.__bases__)

        return parent_annotations | type(self).__annotations__

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        return {
            field: getattr(self, field)
            for field in self.fields
            if exclude is None or field not in exclude
        }


@dataclass_transform(kw_only_default=True)
class DataClass(Serializable):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__post_init__()

    def __post_init__(self):
        pass
