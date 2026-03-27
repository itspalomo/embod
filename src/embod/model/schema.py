from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, cast

from pydantic import TypeAdapter

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]

SchemaType = TypeVar("SchemaType", bound="SchemaModel")


@dataclass(slots=True, frozen=True)
class SchemaModel:
    @classmethod
    def model_validate(cls: type[SchemaType], data: object) -> SchemaType:
        adapter: TypeAdapter[SchemaType] = TypeAdapter(cls)
        return adapter.validate_python(data)

    @classmethod
    def model_validate_json(cls: type[SchemaType], raw: str) -> SchemaType:
        adapter: TypeAdapter[SchemaType] = TypeAdapter(cls)
        return adapter.validate_json(raw)

    @classmethod
    def model_json_schema(cls) -> dict[str, JsonValue]:
        schema = TypeAdapter(cls).json_schema()
        return cast(dict[str, JsonValue], schema)

    def model_dump(self) -> dict[str, JsonValue]:
        dumped = TypeAdapter(type(self)).dump_python(self, mode="json")
        if not isinstance(dumped, dict):
            raise TypeError("Schema models must dump to an object")
        return cast(dict[str, JsonValue], dumped)

    def model_dump_json(self, indent: int | None = None) -> str:
        return TypeAdapter(type(self)).dump_json(self, indent=indent).decode("utf-8")
