from logging import getLogger
from threading import Lock, Thread

from yaml import YAMLError

from testbenchmanager.configuration import (
    ConfigurationDirectory,
    ConfigurationManager,
    ConfigurationScope,
)

from .experiment_configuration import ExperimentConfiguration
from .experiment_context import ExperimentContext
from .experiment_run import ExperimentRun
from .run_registry import run_registry

logger = getLogger(__name__)
# TODO: better exception names


class ExperimentManager:

    def inject_configuration_manager(
        self, configuration_manager: ConfigurationManager
    ) -> None:
        self._config_dir = configuration_manager.get_configuration_directory(
            ConfigurationScope.EXPERIMENTS
        )

    def __init__(self) -> None:
        self._config_dir: ConfigurationDirectory | None = None
        self._experiment_lock: Lock = Lock()
        self._run_uid_counter: int = 0

    def list_experiments(self) -> list[str]:
        if self._config_dir is None:
            raise RuntimeError(
                "Configuration manager not injected. Cannot list experiments."
            )
        return [
            uid
            for uid in self._config_dir.configuration_uids
            if uid
            == ExperimentConfiguration.model_validate(
                self._config_dir.get_contents(uid)
            ).metadata.uid
        ]

    def build_experiment_config(
        self, configuration_uid: str
    ) -> ExperimentConfiguration:
        if self._config_dir is None:
            raise RuntimeError(
                "Configuration manager not injected. Cannot build experiment configuration."
            )
        try:
            configuration = ExperimentConfiguration.model_validate(
                self._config_dir.get_contents(configuration_uid)
            )
        except (FileNotFoundError, YAMLError) as e:
            logger.info(
                "Failed to load experiment configuration with configuration UID '%s': %s",
                configuration_uid,
                e,
            )
            raise e

        return configuration

    def _generate_run_uid(self) -> str:
        run_uid = str(self._run_uid_counter)
        self._run_uid_counter += 1
        return run_uid

    def run_experiment(self, configuration_uid: str) -> str:
        if not self._experiment_lock.acquire(blocking=False):
            logger.error("Failed to acquire experiment lock")
            raise RuntimeError("Yo something else is running!")  # TODO: more specific

        run_uid = self._generate_run_uid()
        experiment = ExperimentRun(
            self.build_experiment_config(configuration_uid),
            ExperimentContext(run_uid=run_uid),
        )
        run_registry.register(run_uid, experiment)

        def run_experiment_thread() -> None:
            experiment.run()
            self._experiment_lock.release()

        thread = Thread(target=run_experiment_thread, daemon=True)
        thread.start()
        return run_uid

    def stop_experiment(self) -> None:
        # TODO: consider changing to stop by run UID
        for run in run_registry.keys:
            run_registry.get(run).stop()


experiment_manager = ExperimentManager()
