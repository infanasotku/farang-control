from uuid import UUID


class CurrentInstanceAliveError(Exception):
    def __init__(self, instance_id: UUID):
        super().__init__(f"Another instance {instance_id} is still alive")


class InstanceDeprecatedError(Exception):
    def __init__(self, instance_id: UUID):
        super().__init__(f"Instance {instance_id} is deprecated")


class InstanceNotRegisteredError(Exception):
    def __init__(self, instance_id: UUID):
        super().__init__(f"Instance {instance_id} is not registered")


class EngineHasNoRuntimeStateError(Exception):
    def __init__(self, engine_id: UUID):
        super().__init__(f"Engine {engine_id} has no runtime owner")
