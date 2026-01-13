from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from .report import Report

T_co = TypeVar("T_co", bound=BaseModel, covariant=True)


class ReportPublisher(Protocol, Generic[T_co]):
    _config: T_co
    def __init__(self, config: T_co) -> None:
        self._config = config

    def publish(self, report: Report) -> None:
        ...

    @classmethod
    def config(cls) -> type[T_co]:
        ...

