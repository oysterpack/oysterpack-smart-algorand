"""
Provides support for KMD wallet-derived Algorand accounts

https://developer.algorand.org/docs/get-details/accounts/create/#wallet-derived-kmd
"""
from dataclasses import dataclass
from typing import Any, Self

from algosdk import kmd
from password_validator import PasswordValidator

from oysterpack.algorand import Mnemonic
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
    """
    KMD service
    """

    def __init__(
        self, url: str, token: str, password_validator: PasswordValidator | None = None
    ):
        """
        :param url: KMD connection URL
        :param token: KMD API token
        :param password_validator: used when creating new wallets to apply password constraints
        """
        self._kmd_client = kmd.KMDClient(kmd_address=url, kmd_token=token)
        self._password_validator = password_validator

    async def list_wallets(self) -> list[Wallet]:
        """
        Returns list of KMD wallets
        """

        wallets = await schedule_blocking_io_task(self._kmd_client.list_wallets)
        return list(map(Wallet._to_wallet, wallets))

    async def get_wallet(self, name: str) -> Wallet | None:
        """
        Returns wallet for the specified name.

        :return : None if the wallet does not exist
        """
        for wallet in await self.list_wallets():
            if wallet.name == name:
                return wallet

        return None

    def __validate_wallet_name_password(
        self, name: str, password: str
    ) -> tuple[str, str]:
        name = name.strip()
        if len(name) == 0:
            raise ValueError("name cannot be blank")
        password = password.strip()
        if len(password) == 0:
            raise ValueError("password cannot be blank")
        if self._password_validator and not self._password_validator.validate(password):
            raise ValueError("password failed validation")
        return (name, password)

    async def create_wallet(self, name: str, password: str) -> Wallet:
        """
        Creates a new wallet using the specified name and password.

        :param name: wallet name - leading and trailing whitespace will be stripped
        :param password: requires a strong password which meets the following criteria:
                         - length must be 30-80
                         - must contain uppercase, lowercase, digits, and symbols
                         - must have no spaces
        :raises KMDHTTPError:
        """
        name, password = self.__validate_wallet_name_password(name, password)
        new_wallet = await schedule_blocking_io_task(
            self._kmd_client.create_wallet, name, password
        )

        return Wallet._to_wallet(new_wallet)

    async def recover_wallet(
        self,
        name: str,
        password: str,
        master_derivation_key: Mnemonic,
    ) -> Wallet:
        """
        Tries to recover a wallet using the specified master derivation key mnemonic.
        The recovered wallet will be empty. Keys will need to be regenerated.

        Notes
        -----
        If a wallet with the same master derivation key already exists but different name already exists, then a new
        wallet will be created with the specified name and password. Both wallets will generate the same accounts.
        KMD wallet passwords cannot be changed. If you lost your wallet password, then you can recover your wallet using
        its master derivation key. If you want to use the same name, then you will need to delete the KMD data directory
        (or use a new data directory) and start over.

        :raises ValueError: if a wallet with the same name already exists
        """

        name, password = self.__validate_wallet_name_password(name, password)
        recovered_wallet = await schedule_blocking_io_task(
            self._kmd_client.create_wallet,
            name,
            password,
            "sqlite",  # driver_name
            master_derivation_key.to_kmd_master_derivation_key(),
        )
        return Wallet._to_wallet(recovered_wallet)
