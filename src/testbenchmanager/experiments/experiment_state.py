from enum import Enum


class ExperimentState(str, Enum):
    """
    Enumeration of experiment states.
    """

    MALFORMED = "malformed"
    READY = "ready"
    RUNNING = "running"
    RUNNING_WITH_WARNINGS = "running_with_warnings"
    STOPPING = "stopping"
    ABORTED = "aborted"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"

    # TODO: Add PAUSED?
