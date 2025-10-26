"""Virtual Instrument implementation."""

import logging
from datetime import datetime
from queue import Empty, Full, Queue
from threading import Condition, Event, Lock
from time import monotonic
from typing import Callable, Generic, Iterator, Optional

from pydantic import BaseModel

from testbenchmanager.common.exceptions import TimeoutException
from testbenchmanager.common.logging import PrefixAdaptor

from .virtual_instrument_state import VirtualInstrumentState, VirtualInstrumentValue

logger = logging.getLogger(__name__)


class VirtualInstrumentMetadata(BaseModel):
    """
    Metadata configuration model for a virtual instrument.
    """

    uid: str
    name: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class VirtualInstrument(Generic[VirtualInstrumentValue]):
    """
    A Virtual Instrument is a representation of a single value or measurement, which can be updated
    over time, and which consumers can subscribe to in order to be notified of updates. Other
    utility methods are provided for other consumption patterns.

    E.g. a temperature reading, a voltage measurement, or a computed value based on other
    instruments.

    Args:
        Generic (_type_): Type of the value held by the virtual instrument.
    """

    def __init__(
        self,
        metadata: VirtualInstrumentMetadata,
        command_callback: Optional[Callable[[VirtualInstrumentValue], None]] = None,
    ) -> None:
        self.metadata: VirtualInstrumentMetadata = metadata

        self._logger = PrefixAdaptor(logger, f"[{self.metadata.uid}] ")

        self._subscriber_callbacks: set[
            Callable[[VirtualInstrumentState[VirtualInstrumentValue]], None]
        ] = set()
        self._state: VirtualInstrumentState[VirtualInstrumentValue]
        self._state_lock: Lock = Lock()
        self._condition: Condition = Condition()
        self._sequence: int = 0
        self._consumer_queues: set[
            Queue[VirtualInstrumentState[VirtualInstrumentValue]]
        ] = set()

        self._command_callback = command_callback

    @property
    def value(self) -> VirtualInstrumentValue:
        """
        Helper method to expose the value from the most recent instrument state

        Returns:
            VirtualInstrumentValue: The most recent value the Virtual Instrument has processed
        """
        return self.get_latest_state().value

    def command(self, value: VirtualInstrumentValue) -> None:
        """
        Attempt to command 'up' to the translation layer to make this virtual instrument read the
        specified value.

        Not all virtual instruments can be commanded. If this instrument cannot be commanded,
        an error will be logged and the command will be ignored.

        Args:
            value (VirtualInstrumentValue): Value to set.
        """
        if self._command_callback is None:
            self._logger.critical(
                "Received command for virtual instrument without command callback set"
            )
            return

        self._command_callback(value)

    def update_state(self, value: VirtualInstrumentValue) -> None:
        """
        Update the internal state of the virtual instrument, which will perform all notification
        side-effects. This is intended to be called by an instrument translation layer object.

        Args:
            value (T): value to update the state to.
        """
        with self._state_lock:
            self._state = VirtualInstrumentState(
                value=value, sequence=self._sequence, timestamp=datetime.now()
            )
            self._sequence += 1
            self._condition.notify_all()

        self._logger.debug("State updated to: %s", self._state)

        # Notify all subscribers
        for callback in self._subscriber_callbacks:
            try:
                callback(self._state)
            except Exception as e:  # pylint: disable=broad-exception-caught
                # We don't want a failing subscriber to fuck everything up for any reason, so we
                # just log it.
                self._logger.warning(
                    "%s raised during subscriber callback: %s", e.__qualname__, str(e)
                )

        for queue in list(self._consumer_queues):
            try:
                queue.put_nowait(self._state)
            except Full:
                try:
                    # Drop the oldest item in the queue.
                    queue.get_nowait()
                    queue.put_nowait(self._state)
                except Empty:
                    # It may be possible for the queue to go from full to empty in this
                    pass

    def subscribe(
        self, callback: Callable[[VirtualInstrumentState[VirtualInstrumentValue]], None]
    ) -> Callable[[], None]:
        """
        Register a callback function to be called when the state of the virtual instrument is
        updated.

        Args:
            callback (Callable[[VirtualInstrumentState[T]], None]): Callback function to register.

        Returns:
            Callable[[], None]: function that can be called to unsubscribe the callback.
        """
        self._subscriber_callbacks.add(callback)

        def unsubscribe() -> None:
            self._subscriber_callbacks.discard(callback)

        return unsubscribe

    def get_latest_state(self) -> VirtualInstrumentState[VirtualInstrumentValue]:
        """
        Get the current state of the virtual instrument.

        Returns:
            VirtualInstrumentState[T]: current state of the virtual instrument.
        """
        with self._state_lock:
            return self._state

    def wait_for(
        self,
        predicate: Callable[[VirtualInstrumentState[VirtualInstrumentValue]], bool],
        timeout: Optional[float] = None,
    ) -> VirtualInstrumentState[VirtualInstrumentValue]:
        """
        Wait for the virtual instrument to reach some condition, then get the state at that point.

        Args:
            predicate (Callable[[VirtualInstrumentState[T]], bool]): Callable to evaluate, taking
            the state as it's only parameter and returning a bool. When this returns true, the state
            will be returned.
            timeout (Optional[float], optional): Maximum time to wait, or None for no timeout.
            Defaults to None.

        Raises:
            TimeoutException: If the timeout is reached before the predicate returns true.

        Returns:
            VirtualInstrumentState[T]: State of the virtual instrument when the predicate returned
            true.
        """
        with self._condition:
            start_time = monotonic()
            while True:
                if predicate(self._state):
                    return self._state

                if timeout is not None:
                    remaining = timeout - (monotonic() - start_time)
                    if remaining <= 0:
                        raise TimeoutException()
                    self._condition.wait(timeout=remaining)
                else:
                    self._condition.wait()

    def as_iterator(
        self, stop: Optional[Event] = None
    ) -> Iterator[VirtualInstrumentState[VirtualInstrumentValue]]:
        """
        Get a representation of this virtual instrument as an iterator. The iterator is lossy; if
        states are updated faster than they are consumed, some states may be skipped, but it will
        always yield the latest state.

        This is ideal for consumers that only care about the most recent state, and don't need to
        process every single state update.

        Args:
            stop (Optional[Event], optional): Event which will terminate the iterator when it set. Defaults to None.

        Yields:
            Iterator[VirtualInstrumentState[T]]: Iterator yielding new states as they arrive.
        """
        last_sequence = -1
        while True:
            if stop is not None and stop.is_set():
                return
            state = self.wait_for(lambda s: s.sequence > last_sequence)
            last_sequence = state.sequence
            yield state

    def as_queue(
        self, maxsize: int = 0
    ) -> Queue[VirtualInstrumentState[VirtualInstrumentValue]]:
        """
        Get a representation of this virtual instrument as a Queue. Every state will be enqueued as
        long as the queue has space, and if the queue is full the oldest state will be dropped to
        make room for the new state.

        This is ideal for consumers that want to process every new state, but don't care about
        having the most recent state if they are falling behind.

        Args:
            maxsize (int, optional): Maximum size of the queue. Defaults to 0, i.e. no max size.

        Returns:
            Queue[VirtualInstrumentState[T]]: Queue which will be filled with states as they are
            generated.
        """
        queue: Queue[VirtualInstrumentState[VirtualInstrumentValue]] = Queue(
            maxsize=maxsize
        )
        self._consumer_queues.add(queue)
        return queue
