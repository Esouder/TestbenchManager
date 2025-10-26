# pylint: skip-file

from typing import Annotated, ClassVar, Protocol

from pydantic import AliasChoices, BaseModel, Field
from pydantic.functional_validators import BeforeValidator


class BaseStep(BaseModel):
    @staticmethod
    def _to_list(v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [v]
        return v

    name: ClassVar[str]
    instruments: Annotated[list[str], BeforeValidator(_to_list)] = Field(
        default_factory=list, validation_alias=AliasChoices("instrument", "instruments")
    )


class Step(Protocol):
    name: ClassVar[str]

    def run(self) -> None: ...

    def stop(self) -> None: ...
