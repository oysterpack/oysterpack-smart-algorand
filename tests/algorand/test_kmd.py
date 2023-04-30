import unittest

from beaker import sandbox

from oysterpack.algorand.kmd import KmdService


class KmdServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_wallets(self):
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
        )
        wallets = await kmd_service.list_wallets()
        self.assertTrue(any(sandbox.kmd.DEFAULT_KMD_WALLET_NAME == wallet.name for wallet in wallets))


if __name__ == "__main__":
    unittest.main()
