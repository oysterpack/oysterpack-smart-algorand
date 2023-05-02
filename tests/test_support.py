from dataclasses import dataclass

from algosdk.transaction import PaymentTxn, wait_for_confirmation
from algosdk.util import algos_to_microalgos
from algosdk.wallet import Wallet
from beaker import sandbox
from beaker.sandbox import SandboxAccount
from ulid import ULID

from oysterpack.algorand import Address, MicroAlgos
from oysterpack.algorand.accounts import get_algo_balance
from oysterpack.algorand.kmd import KmdService, WalletSession
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task


async def sandbox_accounts() -> list[SandboxAccount]:
    """
    :return: sandbox accounts sorted by ALGO balance from lowest to highest
    """

    accounts = await schedule_blocking_io_task(sandbox.get_accounts)
    account_balances = {
        account.address: await get_algo_balance(
            Address(account.address),
            sandbox.get_algod_client(),
        )
        for account in accounts
    }

    def key(sandbox_account: SandboxAccount) -> int:
        return account_balances[sandbox_account.address]

    return sorted(accounts, key=key)


@dataclass
class WalletAccount:
    wallet: WalletSession
    account: Address


def sandbox_kmd_service() -> KmdService:
    return KmdService(
        url=sandbox.kmd.DEFAULT_KMD_ADDRESS,
        token=sandbox.kmd.DEFAULT_KMD_TOKEN,
    )


async def sandbox_default_wallet() -> Wallet:
    return await schedule_blocking_io_task(sandbox.kmd.get_sandbox_default_wallet)


async def create_sandbox_wallet() -> WalletSession:
    name = str(ULID())
    password = str(ULID())
    kmd_service = sandbox_kmd_service()
    await kmd_service.create_wallet(name, password)
    return await kmd_service.connect(name, password, sandbox.get_algod_client())


async def fund_account(account: Address, amt: MicroAlgos | None = None):
    """
    :param account: account to fund
    :param amt: if None, then it defaults to 1 ALGO
    """
    algod_client = sandbox.get_algod_client()
    funder = (await sandbox_accounts()).pop()
    txn = PaymentTxn(
        sender=Address(funder.address),
        receiver=account,
        amt=amt if amt else algos_to_microalgos(1),
        sp=await schedule_blocking_io_task(algod_client.suggested_params),
    )

    signed_txn = await schedule_blocking_io_task(
        (await sandbox_default_wallet()).sign_transaction, txn
    )
    txid = await schedule_blocking_io_task(algod_client.send_transaction, signed_txn)
    await schedule_blocking_io_task(wait_for_confirmation, algod_client, txid)
