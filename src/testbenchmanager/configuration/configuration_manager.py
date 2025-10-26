
import logging
from enum import Enum
from pathlib import Path

from .configuration_directory import ConfigurationDirectory

logger = logging.getLogger(__name__)


class ConfigurationScope(str, Enum):
    INSTRUMENTS = "instruments"

class ConfigurationManager:

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
        return ConfigurationDirectory(self._root, Path(scope.value))
