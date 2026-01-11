from fastapi import APIRouter, HTTPException, status

from testbenchmanager.api.transmission_structures.experiment import (
    ExperimentInfoTransmissionStructure,
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
def get_experiment_info(uid: str) -> ExperimentInfoTransmissionStructure:

    experiment = experiment_manager.get_experiment(uid)
    return ExperimentInfoTransmissionStructure(
        uid=experiment.metadata.uid,
        name=experiment.metadata.name,
        description=experiment.metadata.description,
        steps=[step.metadata.uid for step in experiment.steps],
    )


@experiment_router.post("/{uid}")
def start_experiment_run(uid: str) -> str:
    """
    Add a new experiment run by UID.

    Args:
        uid (str): UID of the experiment to add.

    Returns:
        str: UID of the newly created experiment run.
    """
    try:
        run_uid = experiment_manager.add_experiment(uid)
        experiment_manager.run_experiment(uid)
        return run_uid
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with UID '{uid}' not found.",
        ) from e
