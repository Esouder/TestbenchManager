from fastapi import APIRouter, HTTPException, status

from testbenchmanager.api.transmission_structures.experiment import (
    RunInfoTransmissionStructure,
    StepInfoTransmissionStructure,
)
from testbenchmanager.experiments.experiment_manager import experiment_manager
from testbenchmanager.experiments.run_registry import run_registry

run_router = APIRouter(prefix="/run")


@run_router.get("/")
def list_experiment_runs() -> list[str]:
    """
    List all available experiment runs.

    Returns:
        list[str]: List of experiment run UIDs.
    """
    return run_registry.keys


@run_router.get("/{uid}/")
def get_run_info(uid: str) -> RunInfoTransmissionStructure:

    run = run_registry.get(uid)
    return RunInfoTransmissionStructure(
        uid=uid,
        experiment_uid=run.experiment_metadata.uid,
        state=run.state,
        start_time=run.start_time.isoformat() if run.start_time else None,
        end_time=run.end_time.isoformat() if run.end_time else None,
    )


@run_router.get("/{uid}/step/")
def list_run_steps(uid: str) -> list[str]:
    """
    List all steps in an experiment run.

    Args:
        uid (str): UID of the experiment run.
    Returns:
        list[str]: List of step UIDs in the experiment run.
    """
    try:
        run = run_registry.get(uid)
        return list(run.steps.keys())
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment run with UID '{uid}' not found.",
        ) from e


@run_router.get("/{uid}/step/{step_uid}/")
def get_run_step_info(uid: str, step_uid: str) -> StepInfoTransmissionStructure:
    """
    Get information about a specific step in an experiment run.

    Args:
        uid (str): UID of the experiment run.
        step_uid (str): UID of the step.
    Returns:
        Step information.
    """

    try:
        run = run_registry.get(uid)
        step = run.steps[step_uid]
        return StepInfoTransmissionStructure(
            uid=step.metadata.uid,
            name=step.metadata.name,
            state=step.state,
            start_time=step.start_time.isoformat() if step.start_time else None,
            end_time=step.end_time.isoformat() if step.end_time else None,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with UID '{step_uid}' in run '{uid}' not found.",
        ) from e


@run_router.post("/stop")
def stop_experiment_run() -> None:
    """
    Stop an experiment run by UID.

    Args:
        uid (str): UID of the experiment run to stop.
    """
    try:
        experiment_manager.stop_experiment()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
