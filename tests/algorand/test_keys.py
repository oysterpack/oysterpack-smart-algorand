import base64
import logging
import unittest

import nacl.exceptions
from algosdk import constants, transaction
from algosdk.account import generate_account
from algosdk.transaction import assign_group_id
from algosdk.util import algos_to_microalgos
from beaker import sandbox

from oysterpack.algorand import Mnemonic, keys
from oysterpack.algorand.keys import AlgoPrivateKey
from oysterpack.core.logging import configure_logging

logger = logging.getLogger(__name__)
configure_logging(logging.DEBUG)


class AlgoPrivateKeyTestCase(unittest.TestCase):
    def test_private_key_length(self):
        for _ in range(10):
            private_key, _public_key = generate_account()
            self.assertEqual(
                keys._algorand_base64_encoded_private_key_len, len(private_key)
            )

    def test_init(self):
        with self.subTest("generate new private key"):
            private_keys = {AlgoPrivateKey() for _ in range(100)}
            self.assertEqual(100, len(private_keys), "all new keys must be unique")

        with self.subTest("create from decoded Algorand private key"):
            private_key, _public_key = generate_account()
            private_key_bytes = base64.b64decode(private_key)
            key = AlgoPrivateKey(private_key_bytes)
            self.assertEqual(private_key_bytes[: constants.key_len_bytes], bytes(key))

        with self.subTest("create from private key bytes"):
            private_key_bytes = base64.b64decode(private_key)[: constants.key_len_bytes]
            key = AlgoPrivateKey(private_key_bytes)
            self.assertEqual(private_key_bytes, bytes(key))

        with self.subTest("create from mnemonic"):
            private_key, _public_key = generate_account()
            private_key_bytes = base64.b64decode(private_key)
            mnenomic = Mnemonic.from_private_key(private_key_bytes)
            self.assertEqual(private_key, mnenomic.to_private_key())
            key = AlgoPrivateKey(mnenomic)
            self.assertEqual(private_key_bytes[: constants.key_len_bytes], bytes(key))
            self.assertEqual(key.mnemonic, mnenomic)

            mnenomic = Mnemonic.from_private_key(
                private_key_bytes[: constants.key_len_bytes]
            )
            self.assertEqual(private_key, mnenomic.to_private_key())
            key = AlgoPrivateKey(mnenomic)
            self.assertEqual(private_key_bytes[: constants.key_len_bytes], bytes(key))
            self.assertEqual(key.mnemonic, mnenomic)

        with self.subTest("create from unsupported type"):
            with self.assertRaises(ValueError) as err:
                AlgoPrivateKey(10)  # type: ignore
            logger.error(err.exception)

        with self.subTest("create from mnenomic str"):
            with self.assertRaises(ValueError) as err:
                # raw string mnenomic is not supported - pass in typesafe Mnemonic
                AlgoPrivateKey(str(mnenomic))
            logger.error(err.exception)

            with self.assertRaises(ValueError) as err:
                AlgoPrivateKey("invalid str")
            logger.error(err.exception)

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

    def test_transaction_signer(self):
        sender = AlgoPrivateKey()
        recipient = AlgoPrivateKey()

        with self.subTest("single transaction"):
            payment = transaction.PaymentTxn(
                sender=sender.signing_address,
                receiver=recipient.signing_address,
                sp=sandbox.get_algod_client().suggested_params(),
                amt=algos_to_microalgos(1),
            )
            sender.sign_transactions(txn_group=[payment], indexes=[0])

        with self.subTest("sign transaction group"):
            txns = []
            for _ in range(3):
                txns.append(
                    transaction.PaymentTxn(
                        sender=sender.signing_address,
                        receiver=recipient.signing_address,
                        sp=sandbox.get_algod_client().suggested_params(),
                        amt=algos_to_microalgos(1),
                    )
                )
            txn_group = assign_group_id(txns)
            sender.sign_transactions(txn_group=txn_group, indexes=list(range(3)))
            # sign the first transaction
            sender.sign_transactions(txn_group=txn_group, indexes=list(range(2)))


if __name__ == "__main__":
    unittest.main()
