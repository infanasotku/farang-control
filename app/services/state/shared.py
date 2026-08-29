from datetime import timedelta
from hashlib import sha256

REPLACEMENT_PERMIT_TTL = timedelta(minutes=10)
REPLACEMENT_PERMIT_RANDOM_BYTES = 32


def digest_replacement_permit(permit: str) -> bytes:
    return sha256(permit.encode()).digest()
