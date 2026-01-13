"""Top-level configuration manager."""

import logging
from enum import Enum
from pathlib import Path

from .configuration_directory import ConfigurationDirectory

logger = logging.getLogger(__name__)


# TODO: Should probably register these at runtime.
class ConfigurationScope(str, Enum):
    """
    Enumeration of configuration scopes.
    These scopes correspond to subdirectories under the main configuration root directory.
    """

    INSTRUMENTS = "instruments"
    EXPERIMENTS = "experiments"
    REPORTS = "reports"


# pylint: disable=too-few-public-methods
# There's not much else to this class. Sorry.
class ConfigurationManager:
    """
    Top-level configuration manager.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

        for directory in ConfigurationScope:
            dir_path = self._root / directory.value
            if not dir_path.is_dir():
                logger.warning(
                    "Configuration directory for scope '%s' does not exist at path: %s",
                    directory.value,
                    dir_path,
                )

    def get_configuration_directory(
        self, scope: ConfigurationScope
    ) -> ConfigurationDirectory:
        """
        Get the configuration directory for a given scope.

        Args:
            scope (ConfigurationScope): The configuration scope.

        Returns:
            ConfigurationDirectory: The configuration directory object for the specified scope.
        """
        return ConfigurationDirectory(self._root, Path(scope.value))
