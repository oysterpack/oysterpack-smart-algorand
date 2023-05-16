"""
AsyncAlgodClient wraps an AlgodClient to enable
"""
from typing import Any, cast

from algosdk.transaction import (
    GenericSignedTransaction,
    SuggestedParams,
    wait_for_confirmation,
)
from algosdk.v2client.algod import AlgodClient

from oysterpack.algorand import Address, TxnId
from oysterpack.algorand.accounts import get_auth_address
from oysterpack.algorand.transactions import suggested_params_with_flat_flee
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task


class AsyncAlgodClient:
    def __init__(self, client: AlgodClient):
        self.__client = client

    async def get_auth_address(self, address: Address) -> Address:
        return await get_auth_address(address, self.__client)

    async def suggested_params_with_flat_flee(
        self, txn_count: int = 1
    ) -> SuggestedParams:
        return await suggested_params_with_flat_flee(self.__client, txn_count)

    async def send_transaction(self, txn: GenericSignedTransaction) -> TxnId:
        return TxnId(
            await schedule_blocking_io_task(
                self.__client.send_transaction,
                txn,
            )
        )

    async def wait_for_confirmation(self, txid: TxnId, wait_rounds: int = 0):
        await schedule_blocking_io_task(
            wait_for_confirmation, self.__client, txid, wait_rounds
        )

    async def check_node_status(self):
        """
        Asserts that the algod node is caught up.

        :raises AssertionError: if failed to connect to algod node
        :raises AssertionError: if algod node is not caught up
        """
        try:
            result = cast(
                dict[str, Any], await schedule_blocking_io_task(self.__client.status)
            )
        except Exception as err:
            raise AssertionError("Failed to connect to Algorand node") from err

        if catchup_time := result["catchup-time"] > 0:
            raise AssertionError(
                f"Algorand node is not caught up: catchup_time={catchup_time}"
            )
