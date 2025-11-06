"""Configuration directory representation."""

from pathlib import Path
from typing import Any, ClassVar

import yaml


class ConfigurationDirectory:
    """
    Represents a directory of configuration files.
    (associated with a configuration scope)
    """

    _suffix: ClassVar[str] = ".yaml"

    def __init__(self, root: Path, path: Path) -> None:
        self._path = root / path
        if not self._path.is_dir():
            raise NotADirectoryError(
                f"Configuration directory path '{self._path}' is not a directory."
            )

    @property
    def configuration_uids(self) -> list[str]:
        """
        Get a list of the uids of the config files in this directory.

        Returns:
            list[str]: list of configuration UIDs (i.e. file names without suffix)
        """
        return [
            file.stem
            for file in self._path.iterdir()
            if file.is_file() and file.suffix == self._suffix
        ]

    def get_contents(self, configuration_uid: str) -> dict[str, Any]:
        """
        Get the contents of a configuration file by it's uid, as a dict.

        Args:
            configuration_uid (str): uid of config file to read

        Raises:
            FileNotFoundError: A configuration file with the given UID was not found.
            RuntimeError: An error occurred while parsing the configuration file.

        Returns:
            dict[str, Any]: contents of the configuration file as a dict
        """
        path = self._path / f"{configuration_uid}{self._suffix}"
        try:
            with path.open("r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file '{path}' not found.") from e
        except yaml.YAMLError as e:
            raise RuntimeError(
                f"Error parsing YAML configuration file '{path}': {e}"
            ) from e
