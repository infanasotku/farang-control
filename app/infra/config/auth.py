from pydantic import BaseModel


class AuthSettings(BaseModel):
    edge_api_key: str
    operator_api_key: str | None = None
