from uuid import UUID


class StateService:
    def __init__(self):
        pass

    async def register_instance(self, *, instance_id: UUID, engine_id: UUID) -> int:
        pass
