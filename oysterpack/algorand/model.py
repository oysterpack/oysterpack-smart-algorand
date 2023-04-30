"""
Algorand typesafe domain model
"""

from dataclasses import dataclass
from typing import Self, cast

from algosdk import constants, mnemonic
from algosdk.logic import get_application_address


class Address(str):
    pass


class AssetId(int):
    pass


class BoxKey(bytes):
    pass


class MicroAlgos(int):
    pass


class TxnId(str):
    pass


class AppId(int):
    """
    Algorand smart contract application ID
    """

    @property
    def address(self) -> Address:
        """
        Generates the smart contract's Algorand address from its app ID
        """
        return Address(get_application_address(self))


@dataclass(slots=True)
class Transaction:
    """
    Transaction info
    """

    txn_id: TxnId
    confirmed_round: int
    note: str | None = None


@dataclass(slots=True)
class AssetHolding:
    """
    Account asset holding.
    """

    amount: int
    asset_id: AssetId
    is_frozen: bool


_25WordList = tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
]


@dataclass(slots=True)
class Mnemonic:
    """Mnemonics are 25 word lists that represent private keys.

    PrivateKey <-> Mnemonic

    https://developer.algorand.org/docs/get-details/accounts/#transformation-private-key-to-25-word-mnemonic
    """

    word_list: _25WordList

    @classmethod
    def from_word_list(cls, word_list: str) -> Self:
        """
        :param word_list: 25 word whitespace delimited list
        """
        words = word_list.strip().split()
        return cls(cast(_25WordList, tuple(words)))

    @classmethod
    def from_private_key(cls, key: bytes) -> Self:
        """
        :param key: first 32 bytes are used as the private key
        """
        word_list = mnemonic._from_key(key[: constants.key_len_bytes])
        return cls.from_word_list(word_list)

    def __post_init__(self):
        """
        Check that the mnemonic is a 25 word list.

        :exception ValueError: if the mnemonic does not consist of 25 words
        """
        if len(self.word_list) != 25:
            raise ValueError("mnemonic must consist of 25 words")

    def to_kmd_master_derivation_key(self) -> str:
        """Converts the word list to the base64 encoded KMD wallet master derivation key"""
        return mnemonic.to_master_derivation_key(str(self))

    def to_private_key(self) -> str:
        """
        Converts the word list to the base64 encoded account private key

        https://developer.algorand.org/docs/get-details/accounts/#transformation-private-key-to-base64-private-key
        """
        return mnemonic.to_private_key(str(self))

    def __str__(self) -> str:
        return " ".join(self.word_list)
