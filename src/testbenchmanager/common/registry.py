from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self) -> None:
        self._registry: dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        if name in self._registry:
            raise KeyError(f"Item with name '{name}' is already registered.")
        self._registry[name] = item

    def get(self, name: str) -> T:
        if name not in self._registry:
            raise KeyError(f"Item with name '{name}' is not registered.")
        return self._registry[name]

    def unregister(self, name: str) -> None:
        if name not in self._registry:
            raise KeyError(f"Item with name '{name}' is not registered.")
        del self._registry[name]

    @property
    def keys(self) -> list[str]:
        return list(self._registry.keys())
