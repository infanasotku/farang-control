from uuid import UUID


class EngineNotFoundError(Exception):
    def __init__(self, engine_id: UUID):
        super().__init__(f"Engine with id {engine_id} is not found")
