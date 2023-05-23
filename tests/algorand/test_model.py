import base64
import logging
import re
import unittest

from algosdk import constants, mnemonic
from algosdk.account import generate_account
from beaker.localnet.kmd import get_localnet_default_wallet

from oysterpack.algorand import AppId, Mnemonic
from oysterpack.core.logging import configure_logging

logger = logging.getLogger(__name__)
configure_logging(logging.DEBUG)


class ModelTestCase(unittest.TestCase):
    def test_app_id(self):
        app_id = AppId(10)
        address = app_id.address
        self.assertIsNotNone(re.match(r"\w{58}", address))

    def test_mnemonic(self) -> None:
        private_key, _public_key = generate_account()
        mnemonic1 = Mnemonic.from_private_key(
            base64.b64decode(private_key)[: constants.key_len_bytes]
        )
        self.assertEqual(private_key, mnemonic.to_private_key(str(mnemonic1)))
        self.assertEqual(mnemonic1.to_private_key(), private_key)

        with self.subTest("when word list len is not 25"):
            with self.assertRaises(ValueError) as err:
                Mnemonic.from_word_list(" ".join(mnemonic1.word_list[:24]))
            logger.error(err.exception)

        with self.subTest("kmd master derivation key"):
            wallet = get_localnet_default_wallet()
            mnemonic1 = Mnemonic.from_word_list(wallet.get_mnemonic())
            self.assertEqual(
                wallet.export_master_derivation_key(),
                mnemonic1.to_kmd_master_derivation_key(),
            )


if __name__ == "__main__":
    unittest.main()
