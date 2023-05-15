"""
Algorand CLI
"""
from dataclasses import dataclass
from typing import Any, cast

from algosdk.v2client.algod import AlgodClient

from oysterpack.algorand.kmd import KmdService


@dataclass(slots=True)
class AlgodConfig:
    url: str
    token: str

    def create_client(self) -> AlgodClient:
        """
        Creates a new AlgodClient

        :raises AssertionError: if failed to connect to the algod node or if the node is not caught up
        """
        client = AlgodClient(
            algod_token=self.token,
            algod_address=self.url,
        )

        try:
            result = cast(dict[str, Any], client.status())
        except Exception as err:
            raise AssertionError("Failed to connect to Algorand node") from err

        if catchup_time := result["catchup-time"] > 0:
            raise AssertionError(
                f"Algorand node is not caught up: catchup_time={catchup_time}"
            )

        return client


@dataclass(slots=True)
class KmdConfig:
    url: str
    token: str

    def create_client(self) -> KmdService:
        """
        Creates a new KmdService
        """
        return KmdService(url=self.url, token=self.token)


@dataclass(slots=True)
class AppConfig:
    algod_config: AlgodConfig
    kmd_config: KmdConfig


@dataclass(slots=True)
class App:
    kmd: KmdService
    algod: AlgodClient

    def __init__(self, config: AppConfig):
        self.kmd = config.kmd_config.create_client()
        self.algod = config.algod_config.create_client()
