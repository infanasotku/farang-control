# Hack for Base.metadata to be available in env.py
# for autogenerate support
from app.infra.database.models import aggregates, engine, state

__all__ = ["engine", "state", "aggregates"]
