import unittest

from algosdk.wallet import Wallet
from beaker import sandbox


class KmdWalletDeleteKeyTestCase(unittest.TestCase):
    @unittest.skip("https://github.com/algorand/go-algorand/issues/5346")
    def test_delete_key(self):
        kmd_client = sandbox.kmd.get_client()

        # create new wallet
        name = "foo"
        password = "bar"
        kmd_client.create_wallet(name, password)
        wallet = Wallet(name, password, kmd_client)

        # generate new wallet account
        address = wallet.generate_key()
        self.assertTrue(address in wallet.list_keys())

        # delete wallet account
        self.assertTrue(wallet.delete_key(address))
        self.assertFalse(address in wallet.list_keys())

        # delete wallet account again
        self.assertFalse(
            wallet.delete_key(address),
            "should return False because the wallet does not contain the account",
        )  # this assertion fails


if __name__ == "__main__":
    unittest.main()
