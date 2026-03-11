from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase): ...


uuidpk = Annotated[UUID, mapped_column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)]
intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
