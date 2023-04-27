"""
ULID
"""
from ulid import ULID


class HashableULID(ULID):
    """
    Enhances ULID to be hashable.
    """

    def __hash__(self) -> int:
        return self.bytes.__hash__()
