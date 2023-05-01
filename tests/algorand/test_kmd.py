import json
import unittest

from algosdk.error import KMDHTTPError
from beaker import sandbox
from password_validator import PasswordValidator
from ulid import ULID

from oysterpack.algorand.keys import AlgoPrivateKey
from oysterpack.algorand.kmd import KmdService

WALLET_WITH_SAME_NAME_ALREADY_EXISTS = "wallet with same name already exists"

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
                WALLET_WITH_SAME_NAME_ALREADY_EXISTS, err_object["message"]
            )

        with self.subTest("create wallet with blank name"):
            name_blank_err_msg = "name cannot be blank"
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name="", password=password)
            self.assertEqual(name_blank_err_msg, str(err.exception))

            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=" ", password=password)
            self.assertEqual(name_blank_err_msg, str(err.exception))

        with self.subTest("create wallet with blank password"):
            password_blank_err_msg = "password cannot be blank"
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=name, password="")
            self.assertEqual(password_blank_err_msg, str(err.exception))

            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=name, password=" ")
            self.assertEqual(password_blank_err_msg, str(err.exception))

    async def test_wallet_creation_with_password_validator(self):
        password_validator = (
            PasswordValidator()
            .min(30)
            .max(80)
            .uppercase()
            .lowercase()
            .symbols()
            .digits()
            .has()
            .no()
            .spaces()
        )
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
            password_validator=password_validator,
        )

        password_failed_err_msg = "password failed validation"
        with self.subTest("password too short"):
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=str(ULID()), password="aA1!")
            self.assertEqual(password_failed_err_msg, str(err.exception))

        with self.subTest("password has spaces"):
            password = f"{ULID()}{str(ULID()).lower()} !@"
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=str(ULID()), password=password)
            self.assertEqual(password_failed_err_msg, str(err.exception))

        with self.subTest("password too long"):
            password = f"{ULID()}{str(ULID()).lower()}{ULID()}{ULID()}!"
            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=str(ULID()), password=password)
            self.assertEqual(password_failed_err_msg, str(err.exception))

    async def test_recover_wallet(self):
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
        )

        with self.subTest("recover wallet using a unique name"):
            name = str(ULID())
            password = str(ULID())
            mdk = AlgoPrivateKey().mnemonic

            wallet = await kmd_service.recover_wallet(
                name=name,
                password=password,
                master_derivation_key=mdk,
            )
            self.assertEqual(name, wallet.name)

        with self.subTest("recover wallet again using the same name"):
            with self.assertRaises(KMDHTTPError) as err:
                await kmd_service.recover_wallet(
                    name=name,
                    password=password,
                    master_derivation_key=mdk,
                )
            err_object = json.loads(str(err.exception))
            self.assertEqual(
                WALLET_WITH_SAME_NAME_ALREADY_EXISTS, err_object["message"]
            )

        with self.subTest("recover wallet again using a different name"):
            name = str(ULID())
            wallet = await kmd_service.recover_wallet(
                name=name,
                password=password,
                master_derivation_key=mdk,
            )
            self.assertEqual(name, wallet.name)

        with self.subTest("recover wallet with blank name"):
            name_blank_err_msg = "name cannot be blank"
            with self.assertRaises(ValueError) as err:
                await kmd_service.recover_wallet(
                    name=" ",
                    password=password,
                    master_derivation_key=mdk,
                )
            self.assertEqual(name_blank_err_msg, str(err.exception))

            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=" ", password=password)
            self.assertEqual(name_blank_err_msg, str(err.exception))

        with self.subTest("create wallet with blank password"):
            password_blank_err_msg = "password cannot be blank"
            with self.assertRaises(ValueError) as err:
                await kmd_service.recover_wallet(
                    name=name,
                    password=" ",
                    master_derivation_key=mdk,
                )
            self.assertEqual(password_blank_err_msg, str(err.exception))

            with self.assertRaises(ValueError) as err:
                await kmd_service.create_wallet(name=name, password=" ")
            self.assertEqual(password_blank_err_msg, str(err.exception))

    async def test_wallet_recovery_with_password_validator(self):
        password_validator = (
            PasswordValidator()
            .min(30)
            .max(80)
            .uppercase()
            .lowercase()
            .symbols()
            .digits()
            .has()
            .no()
            .spaces()
        )
        kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
            password_validator=password_validator,
        )
        mdk = AlgoPrivateKey().mnemonic

        password_failed_err_msg = "password failed validation"
        with self.subTest("password too short"):
            with self.assertRaises(ValueError) as err:
                await kmd_service.recover_wallet(
                    name=str(ULID()), password="aA1!", master_derivation_key=mdk
                )
            self.assertEqual(password_failed_err_msg, str(err.exception))

        with self.subTest("password has spaces"):
            password = f"{ULID()}{str(ULID()).lower()} !@"
            with self.assertRaises(ValueError) as err:
                await kmd_service.recover_wallet(
                    name=str(ULID()),
                    password=password,
                    master_derivation_key=mdk,
                )
            self.assertEqual(password_failed_err_msg, str(err.exception))

        with self.subTest("password too long"):
            password = f"{ULID()}{str(ULID()).lower()}{ULID()}{ULID()}!"
            with self.assertRaises(ValueError) as err:
                await kmd_service.recover_wallet(
                    name=str(ULID()),
                    password=password,
                    master_derivation_key=mdk,
                )
            self.assertEqual(password_failed_err_msg, str(err.exception))


class WalletSessionServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # SETUP
        self.kmd_service = KmdService(
            url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
            token=sandbox.kmd.DEFAULT_KMD_TOKEN,
        )

        # create a new wallet
        self.name = str(ULID())
        self.password = str(ULID())
        self.wallet = await self.kmd_service.create_wallet(
            name=self.name,
            password=self.password,
        )

    async def test_connect(self):
        wallet_session = await self.kmd_service.connect(self.name, self.password)
        self.assertEqual(self.name, wallet_session.wallet_name)

    async def test_export_master_derivation_key(self):
        wallet_session = await self.kmd_service.connect(self.name, self.password)
        mdk = await wallet_session.export_master_derivation_key()

        # recover the wallet using the master derivation key with a different name
        name = str(ULID())
        await self.kmd_service.recover_wallet(
            name=name,
            password=self.password,
            master_derivation_key=mdk,
        )

    async def test_rename(self):
        wallet_session = await self.kmd_service.connect(self.name, self.password)
        new_name = str(ULID())
        await wallet_session.rename(new_name)
        self.assertEqual(new_name, wallet_session.wallet_name)

        with self.subTest("blank name"):
            with self.assertRaises(ValueError) as err:
                await wallet_session.rename(" ")
            self.assertEqual("wallet name cannot be blank", str(err.exception))

        with self.subTest("rename to same name"):
            with self.assertRaises(ValueError) as err:
                await wallet_session.rename(new_name)
            self.assertEqual(
                "new wallet name cannot be the same as the current wallet name",
                str(err.exception),
            )

        with self.subTest("rename using a name that already exists"):
            with self.assertRaises(KMDHTTPError) as err:
                await wallet_session.rename(sandbox.kmd.DEFAULT_KMD_WALLET_NAME)
            err_object = json.loads(str(err.exception))
            self.assertEqual(
                WALLET_WITH_SAME_NAME_ALREADY_EXISTS, err_object["message"]
            )


if __name__ == "__main__":
    unittest.main()
