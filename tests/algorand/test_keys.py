import logging
import unittest

import nacl.exceptions

from oysterpack.algorand.keys import AlgoPrivateKey
from oysterpack.core.logging import configure_logging

logger = logging.getLogger(__name__)
configure_logging(logging.DEBUG)


class AlgoPrivateKeyTestCase(unittest.TestCase):
    def test_init(self):
        with self.subTest("generate new private key"):
            private_keys = {AlgoPrivateKey() for _ in range(100)}
            self.assertEqual(100, len(private_keys), "all new keys must be unique")

    def test_public_keys(self):
        private_key = AlgoPrivateKey()
        public_keys = private_key.public_keys
        self.assertEqual(public_keys.signing_address, private_key.signing_address)
        self.assertEqual(public_keys.encryption_address, private_key.encryption_address)

    def test_signing_msgs(self):
        private_key = AlgoPrivateKey()

        msg = b"data"
        signed_message = private_key.sign(msg)

        self.assertTrue(
            private_key.signing_address.verify_message(
                message=msg,
                signature=signed_message.signature,
            )
        )

        with self.subTest("verify invalid message"):
            self.assertFalse(
                private_key.signing_address.verify_message(
                    b"other msg", signed_message.signature
                )
            )

        with self.subTest("verify invalid message"):
            with self.assertRaises(nacl.exceptions.ValueError) as err:
                private_key.signing_address.verify_message(msg, b"invalid signature")
            logger.error(err.exception)

    def test_encryption(self):
        sender = AlgoPrivateKey()
        recipient = AlgoPrivateKey()

        msg = b"data"
        encrypted_msg = sender.encrypt(msg, recipient.encryption_address)

        self.assertEqual(
            msg, recipient.decrypt(encrypted_msg, sender.encryption_address)
        )


if __name__ == "__main__":
    unittest.main()
