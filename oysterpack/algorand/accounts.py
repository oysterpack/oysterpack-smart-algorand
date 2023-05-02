"""
Provides support for working with Algorand accounts
"""
from typing import Any, cast

from algosdk.v2client.algod import AlgodClient

from oysterpack.algorand import Address, MicroAlgos
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task


class AccountDoesNotExistError(Exception):
    """
    Raised if the Algorand account does not exist on-chain.
    """


async def get_auth_address(address: Address, algod_client: AlgodClient) -> Address:
    """
    Returns the authorized signing account for the specified address. This only applies to rekeyed acccounts.
    If the account is not rekeyed, then the account is the authorized account, i.e., the account signs for itself.
    """

    account_info = cast(
        dict[str, Any],
        await schedule_blocking_io_task(algod_client.account_info, address, "all"),
    )
    if "auth-addr" in account_info:
        return Address(account_info["auth-addr"])
    return address


async def get_algo_balance(address: Address, algod_client: AlgodClient) -> MicroAlgos:
    """
    Returns the authorized signing account for the specified address. This only applies to rekeyed acccounts.
    If the account is not rekeyed, then the account is the authorized account, i.e., the account signs for itself.
    """

    account_info = cast(
        dict[str, Any],
        await schedule_blocking_io_task(algod_client.account_info, address, "all"),
    )

    return MicroAlgos(account_info["amount"])
