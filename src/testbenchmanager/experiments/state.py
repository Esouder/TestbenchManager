from enum import Enum


class State(str, Enum):
    """
    Enumeration of experiment and step states.
    """

    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETE = "completed"
    # TODO: Add PAUSED?


class Outcome(str, Enum):
    """
    Enumeration of experiment and step outcomes.
    """

    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABORTED = "aborted"
