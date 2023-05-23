from dataclasses import dataclass

from algosdk.transaction import PaymentTxn
from algosdk.util import algos_to_microalgos
from algosdk.wallet import Wallet
from beaker import localnet
from beaker.localnet import LocalAccount
from ulid import ULID

from oysterpack.algorand import Address, MicroAlgos
from oysterpack.algorand.accounts import get_algo_balance
from oysterpack.algorand.kmd import KmdService, WalletSession
from oysterpack.algorand.transactions import send_transaction
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task


async def localnet_accounts() -> list[LocalAccount]:
    """
    :return: localnet accounts sorted by ALGO balance from lowest to highest
    """

    accounts = await schedule_blocking_io_task(localnet.get_accounts)
    account_balances = {
        account.address: await get_algo_balance(
            Address(account.address),
            localnet.get_algod_client(),
        )
        for account in accounts
    }

    def key(local_account: LocalAccount) -> int:
        return account_balances[local_account.address]

    return sorted(accounts, key=key)


@dataclass
class WalletAccount:
    wallet: WalletSession
    account: Address


def localnet_kmd_service() -> KmdService:
    return KmdService(
        url=localnet.kmd.DEFAULT_KMD_ADDRESS,
        token=localnet.kmd.DEFAULT_KMD_TOKEN,
    )


async def localnet_default_wallet() -> Wallet:
    return await schedule_blocking_io_task(localnet.kmd.get_localnet_default_wallet)


async def create_localnet_wallet() -> WalletSession:
    name = str(ULID())
    password = str(ULID())
    kmd_service = localnet_kmd_service()
    await kmd_service.create_wallet(name, password)
    return await kmd_service.connect(name, password, localnet.get_algod_client())


async def fund_account(account: Address, amt: MicroAlgos | None = None):
    """
    :param account: account to fund
    :param amt: if None, then it defaults to 1 ALGO
    """
    algod_client = localnet.get_algod_client()
    funder = (await localnet_accounts()).pop()
    txn = PaymentTxn(
        sender=Address(funder.address),
        receiver=account,
        amt=amt if amt else algos_to_microalgos(1),
        sp=await schedule_blocking_io_task(algod_client.suggested_params),
    )

    signed_txn = await schedule_blocking_io_task(
        (await localnet_default_wallet()).sign_transaction,
        txn,
    )
    await send_transaction(algod_client, signed_txn)
