from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class DataPoint(Generic[T]):
    timestamp: datetime
    value: T
