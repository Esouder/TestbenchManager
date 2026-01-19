from typing import Callable

from .state import Outcome, State


class GenericStateful:
    outcome: Outcome | None

    def __init__(self) -> None:
        super().__init__()
        self._state: State = State.READY
        self.outcome = None
        self._state_subscriber_callbacks: list[Callable[[State], None]] = []

    def subscribe_to_state_change(
        self, callback: Callable[[State], None]
    ) -> Callable[[], None]:
        self._state_subscriber_callbacks.append(callback)

        def unsubscribe() -> None:
            self._state_subscriber_callbacks.remove(callback)

        return unsubscribe

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, value: State) -> None:
        self._state = value
        for callback in self._state_subscriber_callbacks:
            callback(value)
