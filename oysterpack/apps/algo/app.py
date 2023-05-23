"""
Algorand CLI
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import tomllib
from algosdk.v2client.algod import AlgodClient

from oysterpack.algorand.algod import AsyncAlgodClient
from oysterpack.algorand.kmd import KmdService


@dataclass(slots=True)
class AlgodConfig:
    url: str
    token: str

    def create_client(self) -> AsyncAlgodClient:
        return AsyncAlgodClient(
            AlgodClient(
                algod_token=self.token,
                algod_address=self.url,
            )
        )


@dataclass(slots=True)
class KmdConfig:
    url: str
    token: str

    def create_client(self) -> KmdService:
        return KmdService(url=self.url, token=self.token)


@dataclass(slots=True)
class AppConfig:
    algod_config: AlgodConfig
    kmd_config: KmdConfig

    @classmethod
    def from_config_file(cls, toml_file: Path) -> Self:
        with open(toml_file, "rb") as config_file:
            config = tomllib.load(config_file)

        algod_config = AlgodConfig(
            token=config["algod"]["token"],
            url=config["algod"]["url"],
        )

        kmd_config = KmdConfig(
            token=config["kmd"]["token"],
            url=config["kmd"]["url"],
        )

        return cls(
            algod_config=algod_config,
            kmd_config=kmd_config,
        )


@dataclass(slots=True)
class App:
    kmd: KmdService
    algod: AsyncAlgodClient

    def __init__(self, config: AppConfig):
        self.kmd = config.kmd_config.create_client()
        self.algod = config.algod_config.create_client()

    async def check_connections(self):
        """
        Checks the KMD and algod node connections.

        :raises AssertionError: if fails to get wallet listing from KMD server
        :raises AssertionError: if the algod node is not caught up
        """
        try:
            await self.kmd.list_wallets()
        except Exception as err:
            raise AssertionError("Failed to connect to KMD node") from err

        await self.algod.check_node_status()
