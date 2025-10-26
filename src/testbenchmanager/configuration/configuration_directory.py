from pathlib import Path
from typing import Any, ClassVar

import yaml


class ConfigurationDirectory:

    _suffix: ClassVar[str] = ".yaml"

    def __init__(self, root: Path, path: Path) -> None:
        self._path = root / path
        if not self._path.is_dir():
            raise NotADirectoryError(
                f"Configuration directory path '{self._path}' is not a directory."
            )
    

    @property
    def configuration_uids(self) -> list[str]:
        return [
            file.stem
            for file in self._path.iterdir()
            if file.is_file() and file.suffix == self._suffix
        ]

    def get_contents(self, configuration_uid: str) -> dict[str, Any]: 
        path = self._path / f"{configuration_uid}{self._suffix}"
        try:
            with path.open("r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Configuration file '{path}' not found."
            ) from e
        except yaml.YAMLError as e:
            raise RuntimeError(
                f"Error parsing YAML configuration file '{path}': {e}"
            ) from e
    
