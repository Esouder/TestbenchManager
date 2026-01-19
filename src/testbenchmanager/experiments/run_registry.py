from testbenchmanager.common.registry import Registry

from .experiment_run import ExperimentRun

run_registry = Registry[ExperimentRun]()
