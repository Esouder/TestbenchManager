from dataclasses import dataclass


@dataclass
class ExperimentContext:
    run_uid: str
    configuration_uid: str
