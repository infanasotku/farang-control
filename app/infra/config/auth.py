from pydantic import BaseModel


class AuthSettings(BaseModel):
    edge_api_key: str
