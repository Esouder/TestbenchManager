"""Basic common registry implementation."""

from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """Generic registry class for managing named items."""

    def __init__(self) -> None:
        self._registry: dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        """
        Register an item with a given name.

        Args:
            name (str): Name to register the item under.
            item (T): Item to register.

        Raises:
            KeyError: If an item with the given name is already registered.
        """
        if name in self._registry:
            raise KeyError(f"Item with name '{name}' is already registered.")
        self._registry[name] = item

    def get(self, name: str) -> T:
        """
        Retrieve an item by its registered name.

        Args:
            name (str): Name of the item to retrieve.

        Raises:
            KeyError: If no item with the given name is registered.

        Returns:
            T: The registered item.
        """
        if name not in self._registry:
            raise KeyError(f"Item with name '{name}' is not registered.")
        return self._registry[name]

    def unregister(self, name: str) -> None:
        """
        Unregister an item by its name.

        Args:
            name (str): Name of the item to unregister.

        Raises:
            KeyError: If no item with the given name is registered.
        """
        if name not in self._registry:
            raise KeyError(f"Item with name '{name}' is not registered.")
        del self._registry[name]

    @property
    def keys(self) -> list[str]:
        """
        Get a list of all item names in the registry

        Returns:
            list[str]: List of registered item names.
        """
        return list(self._registry.keys())


class ClassRegistry(Registry[type[T]], Generic[T]):
    """Registry specifically for classes."""

    def register_class(self):
        """Decorator to register a class in the registry."""

        def decorator(cls: type[T]) -> type[T]:
            self.register(cls.__qualname__, cls)
            return cls

        return decorator
