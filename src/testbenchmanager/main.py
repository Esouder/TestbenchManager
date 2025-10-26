import argparse
import logging
from pathlib import Path

from testbenchmanager.configuration import ConfigurationManager, ConfigurationScope
from testbenchmanager.instruments import InstrumentConfiguration, InstrumentManager
from testbenchmanager.instruments.translation.translators import *  # Ensure translators are registered
from testbenchmanager.instruments.virtual import virtual_instrument_registry

parser = argparse.ArgumentParser(description="Testbench Manager")
parser.add_argument(
    "--config-root",
    type=Path,
    required=True,
    help="Path to the root configuration directory",
)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    args = parser.parse_args()
    config_root = args.config_root
    config_manager = ConfigurationManager(root=config_root)
    instrument_config_dir = config_manager.get_configuration_directory(
        ConfigurationScope.INSTRUMENTS
    )
    instrument_manager_instance = InstrumentManager()

    instrument_config = InstrumentConfiguration.model_validate(instrument_config_dir.get_contents(instrument_config_dir.configuration_uids[0]))

    instrument_manager_instance.load_from_configuration(instrument_config)

    logger.info("Loaded instrument configuration: %s", instrument_config.name)

    # For demonstration purposes, list registered virtual instruments
    logger.info("Registered virtual instruments:")
    for uid, instrument in virtual_instrument_registry._registry.items():
        logger.info("UID: %s, Instrument: %s", uid, instrument)
    
    # Keep the application running to allow translators to operate
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Shutting down Testbench Manager.")
        instrument_manager_instance.stop_all_translators()



