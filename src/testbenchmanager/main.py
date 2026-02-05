# pylint: skip-file
# TODO: Remove skip-file when possible

import argparse
import logging
from pathlib import Path

import uvicorn

from testbenchmanager.api import api
from testbenchmanager.configuration import ConfigurationManager
from testbenchmanager.experiments.experiment_manager import experiment_manager
from testbenchmanager.experiments.steps import *  # Ensure steps are registered
from testbenchmanager.instruments import instrument_manager
from testbenchmanager.instruments.translation.translators import *  # Ensure translators are registered
from testbenchmanager.report_generator.report_manager import report_manager
from testbenchmanager.report_generator.report_publishers import *  # Ensure report publishers are registered

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

    instrument_manager.inject_configuration_manager(config_manager)
    instrument_manager.load_all_configurations()

    report_manager.inject_configuration_manager(config_manager)
    report_manager.load_all_configurations()

    experiment_manager.inject_configuration_manager(config_manager)

    # Keep the application running to allow translators to operate
    try:
        uvicorn.run(api, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Shutting down Testbench Manager.")
        instrument_manager.stop_all_translators()
