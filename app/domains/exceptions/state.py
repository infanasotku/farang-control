from uuid import UUID


class CurrentInstanceAliveError(Exception):
    def __init__(self, instance_id: UUID):
        super().__init__(f"Another instance {instance_id} is still alive")


class InstanceDeprecatedError(Exception):
    def __init__(self, instance_id: UUID):
        super().__init__(f"Instance {instance_id} is deprecated")
