import decimal
import json
import unittest

from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.error import InvalidThresholdError, KMDHTTPError
from algosdk.transaction import (
    Multisig,
    MultisigTransaction,
    PaymentTxn,
    wait_for_confirmation,
)
from algosdk.util import algos_to_microalgos
from beaker import localnet
from password_validator import PasswordValidator
from ulid import ULID

from oysterpack.algorand.accounts import get_auth_address
from oysterpack.algorand.keys import AlgoPrivateKey
from oysterpack.algorand.kmd import KmdService
from oysterpack.algorand.transactions import (
    create_rekey_txn,
    send_transaction,
    suggested_params_with_flat_flee,
)
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task
from tests.test_support import fund_account

WALLET_WITH_SAME_NAME_ALREADY_EXISTS = "wallet with same name already exists"


class KmdServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_wallets(self):
        kmd_service = KmdService(
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
        )
        wallets = await kmd_service.list_wallets()
        self.assertTrue(
            any(
                localnet.kmd.DEFAULT_KMD_WALLET_NAME == wallet.name
                for wallet in wallets
            )
        )

    async def test_get_wallet(self):
        kmd_service = KmdService(
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
        )
        wallet = await kmd_service.get_wallet(localnet.kmd.DEFAULT_KMD_WALLET_NAME)
        self.assertIsNotNone(wallet)
        self.assertEqual(localnet.kmd.DEFAULT_KMD_WALLET_NAME, wallet.name)

        with self.subTest("wallet does not exist"):
            self.assertIsNone(await kmd_service.get_wallet(str(ULID())))

    async def test_create_wallet(self):
        kmd_service = KmdService(
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
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
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
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
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
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
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
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
        self.kmd_service = KmdService(
            url=localnet.kmd.DEFAULT_KMD_ADDRESS,
            token=localnet.kmd.DEFAULT_KMD_TOKEN,
        )

        # create a new wallet
        self.name = str(ULID())
        self.password = str(ULID())
        self.wallet = await self.kmd_service.create_wallet(
            name=self.name,
            password=self.password,
        )

    async def test_connect(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        self.assertEqual(self.name, wallet_session.wallet_name)

    async def test_export_master_derivation_key(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        mdk = await wallet_session.export_master_derivation_key()

        # recover the wallet using the master derivation key with a different name
        name = str(ULID())
        await self.kmd_service.recover_wallet(
            name=name,
            password=self.password,
            master_derivation_key=mdk,
        )

    async def test_rename(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
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
                await wallet_session.rename(localnet.kmd.DEFAULT_KMD_WALLET_NAME)
            err_object = json.loads(str(err.exception))
            self.assertEqual(
                WALLET_WITH_SAME_NAME_ALREADY_EXISTS, err_object["message"]
            )

    async def test_account_management(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        self.assertEqual(0, len(await wallet_session.list_accounts()))

        address = await wallet_session.generate_account()
        self.assertTrue(await wallet_session.contains_account(address))

        with self.subTest(
            "`contains_account` should return false for unregistered accounts"
        ):
            self.assertFalse(
                await wallet_session.contains_account(AlgoPrivateKey().signing_address)
            )

        with self.subTest("delete a registered account"):
            await wallet_session.delete_account(address)
            self.assertFalse(await wallet_session.contains_account(address))
            await wallet_session.delete_account(address)

        with self.subTest("deleting an unregistered account is a noop"):
            await wallet_session.delete_account(address)

    async def test_export_private_key(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )

        sender = await wallet_session.generate_account()
        private_key_mnemonic = await wallet_session.export_private_key(sender)

        # verify that the exported private key corresponds to the account
        # by signing a transaction using the KMD wallet and directly using the exported the private key
        # the signatures should match
        receiver = AlgoPrivateKey()
        payment_txn = PaymentTxn(
            sender=sender,
            receiver=receiver.signing_address,
            amt=algos_to_microalgos(1),
            sp=localnet.get_algod_client().suggested_params(),
        )
        signed_txn_1 = await wallet_session.sign_transaction(payment_txn)
        signed_txn_2 = payment_txn.sign(private_key_mnemonic.to_private_key())
        self.assertEqual(signed_txn_1.signature, signed_txn_2.signature)

    async def test_sign_transaction(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        sender = await wallet_session.generate_account()
        await fund_account(sender)

        auth_account = await wallet_session.generate_account()
        await fund_account(auth_account)

        await wallet_session.rekey(sender, auth_account)

        with self.subTest("sign transaction from rekeyed account"):
            receiver = await wallet_session.generate_account()
            txn = PaymentTxn(
                sender=sender,
                receiver=receiver,
                amt=algos_to_microalgos(decimal.Decimal(0.1)),  # type: ignore
                sp=await schedule_blocking_io_task(
                    localnet.get_algod_client().suggested_params
                ),
            )

            signed_txn = await wallet_session.sign_transaction(txn)
            # verify signed transaction by sending it and ensuring it is successful
            algod_client = localnet.get_algod_client()
            txid = await schedule_blocking_io_task(
                algod_client.send_transaction, signed_txn
            )
            await schedule_blocking_io_task(wait_for_confirmation, algod_client, txid)

        with self.subTest(
            "sign transaction with a rekeyed account that doesn't exist in the waller"
        ):
            auth_account_2 = AlgoPrivateKey()
            await wallet_session.rekey(sender, auth_account_2.signing_address)

            with self.assertRaises(AssertionError) as err:
                await wallet_session.sign_transaction(txn)
            self.assertEqual(
                "sender is rekeyed, and the wallet does not contain authorized account",
                str(err.exception),
            )

    async def test_transaction_signer(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        sender = await wallet_session.generate_account()
        await fund_account(sender)

        receiver = await wallet_session.generate_account()
        txn = PaymentTxn(
            sender=sender,
            receiver=receiver,
            amt=algos_to_microalgos(decimal.Decimal(0.1)),  # type: ignore
            sp=await schedule_blocking_io_task(
                localnet.get_algod_client().suggested_params
            ),
        )

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn,
                wallet_session,
            )
        )
        await schedule_blocking_io_task(atc.execute, localnet.get_algod_client(), 2)

    async def test_rekeying(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        sender = await wallet_session.generate_account()
        await fund_account(sender)

        auth_account = await wallet_session.generate_account()
        await fund_account(auth_account)

        await wallet_session.rekey(sender, auth_account)
        self.assertEqual(
            auth_account, await get_auth_address(sender, localnet.get_algod_client())
        )

        await wallet_session.rekey_back(sender)
        self.assertEqual(
            sender, await get_auth_address(sender, localnet.get_algod_client())
        )

    async def test_multisig(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        account_1 = await wallet_session.generate_account()
        account_2 = await wallet_session.generate_account()

        self.assertEqual(0, len(await wallet_session.list_multisigs()))

        with self.subTest("import multisig"):
            multisig = Multisig(
                version=1,
                threshold=2,
                addresses=[account_1, account_2],
            )
            await wallet_session.import_multisig(multisig)
            self.assertTrue(await wallet_session.contains_multisig(multisig.address()))
            multisigs = await wallet_session.list_multisigs()
            self.assertEqual(1, len(multisigs))
            self.assertEqual(multisig, multisigs[multisig.address()])
            self.assertEqual(
                multisig, await wallet_session.export_multisig(multisig.address())
            )

        with self.subTest("import multisig that already exists in the wallet"):
            await wallet_session.import_multisig(multisig)
            multisigs = await wallet_session.list_multisigs()
            self.assertEqual(1, len(multisigs))

        with self.subTest("delete multisig"):
            await wallet_session.delete_multisig(multisig.address())
            self.assertFalse(await wallet_session.contains_multisig(multisig.address()))
            self.assertIsNone(await wallet_session.export_multisig(multisig.address()))

        with self.subTest("delete multisig that does not exist in the wallet"):
            await wallet_session.delete_multisig(multisig.address())

        with self.subTest("import multisig that has no accounts in the wallet"):
            account_3 = AlgoPrivateKey()
            account_4 = AlgoPrivateKey()
            with self.assertRaises(AssertionError):
                await wallet_session.import_multisig(
                    Multisig(
                        version=1,
                        threshold=2,
                        addresses=[
                            account_3.signing_address,
                            account_4.signing_address,
                        ],
                    )
                )

        with self.subTest("import multisig with only 1 account in this wallet"):
            multisig = Multisig(
                version=1,
                threshold=2,
                addresses=[
                    account_1,
                    account_4.signing_address,
                ],
            )
            await wallet_session.import_multisig(multisig)
            self.assertTrue(await wallet_session.contains_multisig(multisig.address()))

        with self.subTest("import invalid multisig"):
            with self.assertRaises(InvalidThresholdError):
                await wallet_session.import_multisig(
                    Multisig(
                        version=1,
                        threshold=3,
                        addresses=[
                            account_1,
                            account_2,
                        ],
                    )
                )

    async def test_sign_multisig_txn(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        account_1 = await wallet_session.generate_account()
        account_2 = await wallet_session.generate_account()
        multisig = Multisig(
            version=1,
            threshold=2,
            addresses=[account_1, account_2],
        )
        await wallet_session.import_multisig(multisig)
        await fund_account(multisig.address())

        account_3 = await wallet_session.generate_account()

        txn = PaymentTxn(
            sender=multisig.address(),
            receiver=account_3,
            amt=algos_to_microalgos(decimal.Decimal(0.1)),  # type: ignore
            sp=await suggested_params_with_flat_flee(localnet.get_algod_client()),
        )
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=txn,
                signer=wallet_session,
            )
        )
        await schedule_blocking_io_task(atc.execute, localnet.get_algod_client(), 2)

        with self.subTest("multisig is not in the wallet"):
            await wallet_session.delete_multisig(multisig.address())
            with self.assertRaises(AssertionError) as err:
                await wallet_session.sign_multisig_transaction(
                    MultisigTransaction(txn, multisig)
                )
            self.assertEqual(
                "multsig does not exist in this wallet", str(err.exception)
            )

        with self.subTest("sign using specified account"):
            await wallet_session.import_multisig(multisig)
            txn = PaymentTxn(
                sender=multisig.address(),
                receiver=account_3,
                amt=algos_to_microalgos(decimal.Decimal(0.1)),  # type: ignore
                sp=await suggested_params_with_flat_flee(localnet.get_algod_client()),
            )
            signed_multisig_txn = await wallet_session.sign_multisig_transaction(
                txn=MultisigTransaction(txn, multisig),
                account=account_1,
            )
            signed_multisig_txn = await wallet_session.sign_multisig_transaction(
                txn=signed_multisig_txn,
                account=account_2,
            )
            await send_transaction(localnet.get_algod_client(), signed_multisig_txn)

        with self.subTest("sign using account that is not part of multisig"):
            with self.assertRaises(AssertionError) as err:
                await wallet_session.sign_multisig_transaction(
                    txn=MultisigTransaction(txn, multisig),
                    account=AlgoPrivateKey().signing_address,
                )
            self.assertEqual(
                "multisig does not contain the specified account", str(err.exception)
            )

        with self.subTest("wallet does not contain the specified account"):
            await wallet_session.delete_account(account_1)
            with self.assertRaises(AssertionError) as err:
                await wallet_session.sign_multisig_transaction(
                    txn=MultisigTransaction(txn, multisig),
                    account=account_1,
                )
            self.assertEqual(
                "signing account does not exist in this wallet", str(err.exception)
            )

    async def test_sign_multisig_txn_using_rekeyed(self):
        wallet_session = await self.kmd_service.connect(
            self.name, self.password, localnet.get_algod_client()
        )
        main_account = await wallet_session.generate_account()
        account_1 = await wallet_session.generate_account()
        account_2 = await wallet_session.generate_account()
        multisig = Multisig(
            version=1,
            threshold=2,
            addresses=[account_1, account_2],
        )
        await wallet_session.import_multisig(multisig)
        await fund_account(main_account)

        # rekey the main account to the multisig
        rekey_txn = create_rekey_txn(
            account=main_account,
            rekey_to=multisig.address(),
            suggested_params=await suggested_params_with_flat_flee(
                localnet.get_algod_client()
            ),
        )
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=rekey_txn,
                signer=wallet_session,
            )
        )
        await schedule_blocking_io_task(atc.execute, localnet.get_algod_client(), 2)

        # send a payment from the main_account to account_3
        # the transaction is signed by the multisig
        account_3 = await wallet_session.generate_account()
        txn = PaymentTxn(
            sender=main_account,
            receiver=account_3,
            amt=algos_to_microalgos(decimal.Decimal(0.1)),  # type: ignore
            sp=await suggested_params_with_flat_flee(localnet.get_algod_client()),
        )
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=txn,
                signer=wallet_session,
            )
        )
        await schedule_blocking_io_task(atc.execute, localnet.get_algod_client(), 2)

        with self.subTest("using specified accounts"):
            txn = PaymentTxn(
                sender=main_account,
                receiver=account_3,
                amt=algos_to_microalgos(decimal.Decimal(0.1)),  # type: ignore
                sp=await suggested_params_with_flat_flee(localnet.get_algod_client()),
            )
            multisig_txn = await wallet_session.sign_multisig_transaction(
                MultisigTransaction(txn, multisig),
                account_1,
            )
            multisig_txn = await wallet_session.sign_multisig_transaction(
                multisig_txn,
                account_2,
            )
            await send_transaction(localnet.get_algod_client(), multisig_txn)


if __name__ == "__main__":
    unittest.main()
