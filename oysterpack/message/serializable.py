"""
Serializable protocol
"""

from typing import Protocol, Self

from oysterpack.core.ulid import HashableULID


class MessageType(HashableULID):
    """
    Message type ID
    """


class Serializable(Protocol):
    """
    Serializable protocol
    """

    @classmethod
    def message_type(cls) -> MessageType:
        """
        Specifies which MessageType is supported for serialization.
        This effectively maps the class type to the MessageType.

        :return: MessageType
        """

    def pack(self) -> bytes:
        """
        Packs the object into bytes
        """

    @classmethod
    def unpack(cls, packed: bytes) -> Self:
        """
        Unpacks the packed bytes into a new instance of Self
        """
