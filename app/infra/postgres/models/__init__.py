# Hack for Base.metadata to be available in env.py
# for autogenerate support
from app.infra.postgres.models import engine, state

__all__ = ["engine", "state"]
