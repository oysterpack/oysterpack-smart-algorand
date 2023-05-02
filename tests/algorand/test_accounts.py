import unittest

from algosdk.transaction import wait_for_confirmation
from beaker import sandbox

from oysterpack.algorand.accounts import get_algo_balance, get_auth_address
from oysterpack.algorand.keys import AlgoPrivateKey
from oysterpack.algorand.transactions import create_rekey_txn
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task
from tests.test_support import fund_account


class AccountsTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_get_auth_addr(self):
        with self.subTest("account is not rekeyed"):
            account = AlgoPrivateKey()
            auth_acct = await get_auth_address(
                account.signing_address, sandbox.get_algod_client()
            )
            self.assertEqual(account.signing_address, auth_acct)

        with self.subTest("account is rekeyed"):
            algod_client = sandbox.get_algod_client()
            account_2 = AlgoPrivateKey()
            await fund_account(account.signing_address)
            txn = create_rekey_txn(
                account.signing_address,
                account_2.signing_address,
                await schedule_blocking_io_task(algod_client.suggested_params),
            )
            signed_txn = account.sign_transactions([txn], [0])[0]
            txid = await schedule_blocking_io_task(
                algod_client.send_transaction, signed_txn
            )
            await schedule_blocking_io_task(wait_for_confirmation, algod_client, txid)

            auth_acct = await get_auth_address(
                account.signing_address, sandbox.get_algod_client()
            )
            self.assertEqual(account_2.signing_address, auth_acct)

    async def test_get_algo_balance(self):
        account = AlgoPrivateKey()
        algod_client = sandbox.get_algod_client()
        algo_balance = await get_algo_balance(account.signing_address, algod_client)
        self.assertEqual(0, algo_balance)


if __name__ == "__main__":
    unittest.main()
