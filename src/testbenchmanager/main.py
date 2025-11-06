# pylint: skip-file
# TODO: Remove skip-file when possible

import argparse
import logging
from pathlib import Path

import uvicorn

from testbenchmanager.api import api
from testbenchmanager.configuration import ConfigurationManager, ConfigurationScope
from testbenchmanager.instruments import InstrumentConfiguration, InstrumentManager
from testbenchmanager.instruments.translation.translators import *  # Ensure translators are registered

parser = argparse.ArgumentParser(description="Testbench Manager")
parser.add_argument(
    "--config-root",
    type=Path,
    required=True,
    help="Path to the root configuration directory",
)

parser.add_argument(
    "--log-level",
    type=str.upper,
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
)


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, parser.parse_args().log_level))
    logger = logging.getLogger(__name__)
    args = parser.parse_args()
    config_root = args.config_root
    config_manager = ConfigurationManager(root=config_root)
    instrument_config_dir = config_manager.get_configuration_directory(
        ConfigurationScope.INSTRUMENTS
    )
    instrument_manager_instance = InstrumentManager()

    instrument_config = InstrumentConfiguration.model_validate(
        instrument_config_dir.get_contents(instrument_config_dir.configuration_uids[0])
    )

    instrument_manager_instance.load_from_configuration(instrument_config)

    logger.info("Loaded instrument configuration: %s", instrument_config.name)

    # Keep the application running to allow translators to operate
    try:
        uvicorn.run(api, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Shutting down Testbench Manager.")
        instrument_manager_instance.stop_all_translators()
