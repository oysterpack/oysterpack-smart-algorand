import json
import unittest

from algosdk.error import KMDHTTPError
from beaker import sandbox
from ulid import ULID

from oysterpack.algorand.kmd import KmdService


class KmdServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_wallets(self):
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
        )
        wallets = await kmd_service.list_wallets()
        self.assertTrue(
            any(
                sandbox.kmd.DEFAULT_KMD_WALLET_NAME == wallet.name for wallet in wallets
            )
        )

    async def test_get_wallet(self):
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
        )
        wallet = await kmd_service.get_wallet(sandbox.kmd.DEFAULT_KMD_WALLET_NAME)
        self.assertIsNotNone(wallet)
        self.assertEqual(sandbox.kmd.DEFAULT_KMD_WALLET_NAME, wallet.name)

        with self.subTest("wallet does not exist"):
            self.assertIsNone(await kmd_service.get_wallet(str(ULID())))

    async def test_create_wallet(self):
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
        )

        with self.subTest("create new wallet with unique name"):
            name = str(ULID())
            password = str(ULID())
            wallet = await kmd_service.create_wallet(name=name, password=password)
            self.assertEqual(name, wallet.name)
            wallet_2 = await kmd_service.get_wallet(name)
            self.assertEqual(wallet, wallet_2)

        with self.subTest("create new wallet using a name that already exists"):
            with self.assertRaises(KMDHTTPError) as err:
                await kmd_service.create_wallet(name=name, password=password)
            err_object = json.loads(str(err.exception))
            self.assertEqual(
                "wallet with same name already exists", err_object["message"]
            )

        with self.subTest("create wallet with blank name"):
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name="", password=password)
            self.assertEqual("name cannot be blank", str(err.exception))

            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=" ", password=password)
            self.assertEqual("name cannot be blank", str(err.exception))

        with self.subTest("create wallet with blank password"):
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=name, password="")
            self.assertEqual("password cannot be blank", str(err.exception))

            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=name, password=" ")
            self.assertEqual("password cannot be blank", str(err.exception))


if __name__ == "__main__":
    unittest.main()
