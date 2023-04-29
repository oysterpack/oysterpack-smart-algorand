import logging
import unittest
from dataclasses import dataclass
from typing import ClassVar, Self

import msgpack

from oysterpack.core.logging import configure_logging
from oysterpack.message import Message, MessageType, Serializable

logger = logging.getLogger(__name__)
configure_logging(level=logging.DEBUG)

pack_failure = False


@dataclass(slots=True)
class Foo(Serializable):
    __MSG_TYPE: ClassVar[MessageType] = MessageType.from_str(
        "01GZ6G1TK5CDF7CMJZJAZ03AHD"
    )

    count: int
    text: str

    @classmethod
    def message_type(cls) -> MessageType:
        return cls.__MSG_TYPE

    def pack(self) -> bytes:
        global pack_failure
        if pack_failure:
            raise ValueError("BOOM!")

        return msgpack.packb((self.count, self.text))

    @classmethod
    def unpack(cls, packed: bytes) -> Self:
        (count, msg) = msgpack.unpackb(packed)
        return cls(
            count=count,
            text=msg,
        )


class MessageTestCase(unittest.TestCase):
    def test_pack_unpack(self) -> None:
        foo = Foo(10, "hello")
        msg = Message.from_serializable(foo)
        msg_2 = Message.unpack(msg.pack())
        self.assertEqual(msg, msg_2)

    def test_unpack_invalid_data(self) -> None:
        with self.assertRaises(ValueError) as err:
            Message.unpack(b"invalid data")
        logger.error(err.exception)

    def test_when_serializable_pack_fails(self) -> None:
        global pack_failure
        pack_failure = True
        foo = Foo(10, "hello")
        try:
            with self.assertRaises(ValueError) as err:
                Message.from_serializable(foo)
            logger.error(err.exception)
        finally:
            pack_failure = False


if __name__ == "__main__":
    unittest.main()
