import unittest

from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from beaker import sandbox

from oysterpack.algorand.accounts import get_auth_address
from oysterpack.algorand.keys import AlgoPrivateKey
from oysterpack.algorand.transactions import (
    create_rekey_back_txn,
    create_rekey_txn,
    suggested_params_with_flat_flee,
)
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task
from tests.test_support import fund_account


class TransactionsTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_rekeying(self):
        algod_client = sandbox.get_algod_client()
        account_1 = AlgoPrivateKey()
        account_2 = AlgoPrivateKey()

        await fund_account(account_1.signing_address)

        txn = create_rekey_txn(
            account_1.signing_address,
            account_2.signing_address,
            await suggested_params_with_flat_flee(algod_client),
        )
        atc = AtomicTransactionComposer()
        atc.add_transaction(TransactionWithSigner(txn, account_1))
        await schedule_blocking_io_task(atc.execute, algod_client, 2)
        self.assertEqual(
            account_2.signing_address,
            await get_auth_address(
                account_1.signing_address, sandbox.get_algod_client()
            ),
        )

        with self.subTest("rekey back"):
            txn = create_rekey_back_txn(
                account_1.signing_address,
                await suggested_params_with_flat_flee(algod_client),
            )
            atc = AtomicTransactionComposer()
            atc.add_transaction(TransactionWithSigner(txn, account_2))
            await schedule_blocking_io_task(atc.execute, algod_client, 2)
            self.assertEqual(
                account_1.signing_address,
                await get_auth_address(
                    account_1.signing_address, sandbox.get_algod_client()
                ),
            )


if __name__ == "__main__":
    unittest.main()
