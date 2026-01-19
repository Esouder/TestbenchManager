from fastapi import APIRouter, HTTPException, status

from testbenchmanager.api.transmission_structures.experiment import (
    ExperimentConfigurationTransmissionStructure,
    StepConfigurationTransmissionStructure,
)
from testbenchmanager.experiments.experiment_manager import experiment_manager

experiment_router = APIRouter(prefix="/experiment")


@experiment_router.get("/")
def list_experiments() -> list[str]:
    """
    List all available experiments.

    Returns:
        list[str]: List of experiment UIDs.
    """
    return experiment_manager.list_experiments()


@experiment_router.get("/{uid}/")
def get_experiment_configuration(
    uid: str,
) -> ExperimentConfigurationTransmissionStructure:

    configuration = experiment_manager.build_experiment_config(uid)
    return ExperimentConfigurationTransmissionStructure(
        metadata=configuration.metadata,
        steps={
            step.metadata.uid: StepConfigurationTransmissionStructure(
                metadata=step.metadata,
                skip_on_previous_failure=step.skip_on_previous_failure,
                skip_on_abort=step.skip_on_abort,
            )
            for step in configuration.steps
        },
    )


@experiment_router.post("/{uid}/")
def start_experiment_run(uid: str) -> str:
    try:
        run_uid = experiment_manager.run_experiment(uid)
        return run_uid
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with UID '{uid}' not found.",
        ) from e
