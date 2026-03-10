# Hack for Base.metadata to be available in env.py
# for autogenerate support
from app.infra.database.models import core

__all__ = ["core"]
