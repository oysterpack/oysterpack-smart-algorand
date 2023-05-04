"""
Provides support for Algorand transactions
"""
from algosdk.transaction import (
    LogicSigTransaction,
    MultisigTransaction,
    PaymentTxn,
    SignedTransaction,
    SuggestedParams,
    wait_for_confirmation,
)
from algosdk.v2client.algod import AlgodClient

from oysterpack.algorand import Address, TxnId
from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task


async def suggested_params_with_flat_flee(
    algod_client: AlgodClient,
    txn_count: int = 1,
) -> SuggestedParams:
    """
    Returns a suggested txn params using the min flat fee.

    :param txn_count: specifies how many transactions to pay for
    """
    if txn_count < 1:
        raise ValueError("txn_count must be >= 1")
    suggested_params = await schedule_blocking_io_task(algod_client.suggested_params)
    suggested_params.fee = suggested_params.min_fee * txn_count
    suggested_params.flat_fee = True
    return suggested_params


async def send_transaction(
    algod_client: AlgodClient,
    txn: SignedTransaction | MultisigTransaction | LogicSigTransaction,
) -> TxnId:
    txid = await schedule_blocking_io_task(algod_client.send_transaction, txn)
    await schedule_blocking_io_task(wait_for_confirmation, algod_client, txid)
    return TxnId(txid)


def create_rekey_txn(
    account: Address,
    rekey_to: Address,
    suggested_params: SuggestedParams,
) -> PaymentTxn:
    """
    Creates a transaction to rekey the account to the specified authorized account.

    NOTE: the transaction must be signed by the current authorized account.
    """

    return PaymentTxn(
        sender=account,
        receiver=account,
        amt=0,
        rekey_to=rekey_to,
        sp=suggested_params,
    )


def create_rekey_back_txn(
    account: Address, suggested_params: SuggestedParams
) -> PaymentTxn:
    """
    Creates a transaction to rekey the account back to itself.

    NOTE: the transaction must be signed by the current authorized account.
    """

    return create_rekey_txn(
        account=account,
        rekey_to=account,
        suggested_params=suggested_params,
    )
