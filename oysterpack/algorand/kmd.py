"""
Provides support for KMD wallet-derived Algorand accounts

https://developer.algorand.org/docs/get-details/accounts/create/#wallet-derived-kmd
"""
from dataclasses import dataclass
from typing import Any, Self

from algosdk import kmd

from oysterpack.core.asyncio.task_manager import schedule_blocking_io_task


@dataclass(slots=True)
class Wallet:
    """
    KMD wallet
    """

    wallet_id: str
    name: str

    @classmethod
    def _to_wallet(cls, data: dict[str, Any]) -> Self:
        return cls(wallet_id=data["id"], name=data["name"])


class KmdService:

    def __init__(self, url: str, token: str):
        self._kmd_client = kmd.KMDClient(kmd_address=url, kmd_token=token)

    async def list_wallets(self) -> list[Wallet]:
        """
        Returns list of KMD wallets
        """

        wallets = await schedule_blocking_io_task(self._kmd_client.list_wallets)
        return list(map(Wallet._to_wallet, wallets))
