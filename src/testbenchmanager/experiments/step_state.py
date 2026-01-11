from enum import Enum


class StepState(str, Enum):
    """
    Enumeration of step states.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    STOPPING = "stopping"
    FAILED = "failed"
    SKIPPED = "skipped"
    RUNNING_WITH_WARNINGS = "running_with_warnings"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
