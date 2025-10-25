from testbenchmanager.common import Registry

from .step import Step


class StepRegistry(Registry[type[Step]]):
    def register_step(self):
        def decorator(step_cls: type[Step]) -> type[Step]:
            self.register(step_cls.name, step_cls)
            return step_cls

        return decorator


step_registry = StepRegistry()
