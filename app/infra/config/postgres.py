from pydantic import BaseModel, Field, computed_field


class PostgreSQLSettings(BaseModel):
    host: str
    password: str
    username: str
    db_name: str

    sql_schema: str = Field(default="public")
    port: int = Field(default=5432)

    @computed_field
    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}" + f"@{self.host}:{self.port}/{self.db_name}"
