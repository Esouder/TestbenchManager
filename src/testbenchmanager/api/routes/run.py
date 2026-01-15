from multiprocessing import Event
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from testbenchmanager.api.transmission_structures.experiment import (
    RunInfoTransmissionStructure,
    StepInfoTransmissionStructure,
)
from testbenchmanager.experiments.experiment_manager import experiment_manager
from testbenchmanager.experiments.experiment_state import ExperimentState
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
        experiment_metadata=run.experiment_metadata,
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
def get_run_step_info(
    uid: str, step_uid: str, change: bool = False, timeout: Optional[float] = None
) -> StepInfoTransmissionStructure:
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
        if change:
            if run.current_step and run.current_step.metadata.uid == step_uid:
                # Wait for the step to complete
                step_completed_event = Event()

                def check_step_state(state: ExperimentState) -> None:
                    if (
                        state != ExperimentState.RUNNING
                        or run.current_step is None
                        or run.current_step.metadata.uid != step_uid
                    ):
                        step_completed_event.set()

                unsubscribe = run.subscribe_to_state_changes(check_step_state)
                if (
                    run.state == ExperimentState.RUNNING
                    and run.current_step
                    and run.current_step.metadata.uid == step_uid
                ):
                    try:
                        step_completed_event.wait(timeout=timeout)
                    except TimeoutError as e:
                        raise HTTPException(
                            status_code=status.HTTP_408_REQUEST_TIMEOUT
                        ) from e
                unsubscribe()
        return StepInfoTransmissionStructure(
            metadata=step.metadata,
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
