import asyncio
from typing import Callable

from fastapi import APIRouter, HTTPException, status

from testbenchmanager.api.transmission_structures.experiment import (
    ExperimentRunTransmissionStructure,
    StepRunTransmissionStructure,
)
from testbenchmanager.experiments.experiment_manager import experiment_manager
from testbenchmanager.experiments.run_registry import run_registry
from testbenchmanager.experiments.state import State

run_router = APIRouter(prefix="/run")

from enum import Enum


class SubscriptableTopics(str, Enum):
    STATE_CHANGE = "state_change"


@run_router.get("/")
def list_experiment_runs() -> list[str]:
    """
    List all available experiment runs.

    Returns:
        list[str]: List of experiment run UIDs.
    """
    return run_registry.keys


@run_router.get("/{run_uid}/")
async def get_run(
    run_uid: str, on: SubscriptableTopics | None = None, timeout: float = 30.0
) -> ExperimentRunTransmissionStructure:
    run = run_registry.get(run_uid)

    if on == SubscriptableTopics.STATE_CHANGE:
        event = asyncio.Event()

        def callback(state: State) -> None:
            event.set()

        unsubscribes: list[Callable[[], None]] = []
        unsubscribes.append(run.subscribe_to_state_change(callback))
        for step in run.steps.values():
            unsubscribes.append(step.subscribe_to_state_change(callback))
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError as e:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Timeout waiting for state change on run '{run_uid}'.",
            ) from e
        finally:
            for unsubscribe in unsubscribes:
                unsubscribe()

    return ExperimentRunTransmissionStructure(
        configuration_uid=run.configuration_uid,
        state=run.state,
        outcome=run.outcome,
        start_time=run.start_time,
        end_time=run.end_time,
        steps={
            step_uid: StepRunTransmissionStructure(
                state=step.state,
                outcome=step.outcome,
                start_time=step.start_time,
                end_time=step.end_time,
            )
            for step_uid, step in run.steps.items()
        },
    )


@run_router.post("/stop/")
def stop_all_runs() -> None:
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
