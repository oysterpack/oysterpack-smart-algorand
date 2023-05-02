"""
:type:`AlgoPrivateKey` adds the capability to encrypt private messages using the same Algorand private key that is used
to sign messages.

Specifically, :type:``AlgoPrivateKey`` supports authenticated encryption, i.e., box encryption:

https://doc.libsodium.org/public-key_cryptography/authenticated_encryption
"""

import base64
from dataclasses import dataclass

from algosdk import constants, mnemonic, transaction
from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.encoding import decode_address, encode_address
from algosdk.transaction import GenericSignedTransaction
from nacl.exceptions import BadSignatureError
from nacl.public import Box, PrivateKey, PublicKey
from nacl.signing import SignedMessage, SigningKey, VerifyKey

from oysterpack.algorand import Address, Mnemonic


class EncryptionAddress(Address):
    """
    Public box encryption key encoded as an Algorand address
    """

    def to_public_key(self) -> PublicKey:
        """
        EncryptionAddress -> PublicKey
        """
        return PublicKey(decode_address(self))


class SigningAddress(Address):
    """
    Public signing key encoded as an Algorand address
    """

    def to_verify_key(self) -> VerifyKey:
        """
        SigningAddress -> VerifyKey
        """
        return VerifyKey(decode_address(self))

    def verify_message(self, message: bytes, signature: bytes) -> bool:
        """
        :return: True if the message has a valid signature
        :raises ValueError: if signature is invalid format
        """
        verify_key = self.to_verify_key()
        try:
            verify_key.verify(message, signature)
            return True
        except BadSignatureError:
            return False


@dataclass(slots=True)
class AlgoPublicKeys:
    signing_address: SigningAddress
    encryption_address: EncryptionAddress


# https://developer.algorand.org/docs/get-details/accounts/#transformation-private-key-to-base64-private-key
_algorand_base64_encoded_private_key_len = 88


class AlgoPrivateKey(PrivateKey, TransactionSigner):
    """
    Algorand private keys can be used to sign and encrypt messages.

    Messages are encrypted using box encryption using the recipient's encryption address.
    The encrypted message can only be decrypted by the intended recipient using its private key
    and the sender's public EncryptionAddress.

    NOTES
    -----
    - Self encrypted messages can be created, i.e., sender == recipient
    -
    """

    def __init__(self, algo_private_key: str | bytes | Mnemonic | None = None):
        """
        :param algo_private_key: If not specified, then a new Algorand private key will be generated.
            The Algorand account private key can be specified in the following formats:
                1. base64 encoded bytes - https://developer.algorand.org/docs/get-details/accounts/#transformation-private-key-to-base64-private-key
                2. raw bytes
                3. Mnemonic
        """
        if algo_private_key is None:
            algo_private_key = generate_account()[0]

        if isinstance(algo_private_key, str):
            if len(algo_private_key) != _algorand_base64_encoded_private_key_len:
                raise ValueError(
                    f"invalid Algorand private key - expected length is {_algorand_base64_encoded_private_key_len}"
                )
            super().__init__(
                base64.b64decode(algo_private_key)[: constants.key_len_bytes]
            )
        elif isinstance(algo_private_key, bytes):
            if len(algo_private_key) == constants.key_len_bytes:
                super().__init__(algo_private_key)
            else:
                super().__init__(algo_private_key[: constants.key_len_bytes])
        elif isinstance(algo_private_key, Mnemonic):
            private_key = algo_private_key.to_private_key()
            private_key_bytes = base64.b64decode(private_key)
            super().__init__(private_key_bytes[: constants.key_len_bytes])
        else:
            raise ValueError(
                "invalid private_key type - must be str | bytes | Mnemonic"
            )

    @property
    def mnemonic(self) -> Mnemonic:
        """
        :return: Algorand private key encoded as a 25-word mnemonic
        """
        return Mnemonic.from_word_list(
            mnemonic.from_private_key(base64.b64encode(bytes(self)).decode())
        )

    @property
    def public_keys(self) -> AlgoPublicKeys:
        return AlgoPublicKeys(
            signing_address=self.signing_address,
            encryption_address=self.encryption_address,
        )

    @property
    def encryption_address(self) -> EncryptionAddress:
        """
        EncryptionAddress is derived from the Algorand account's private key.

        :return: base32 encoded public encryption key
        """
        return EncryptionAddress(Address(encode_address(bytes(self.public_key))))

    @property
    def signing_key(self) -> SigningKey:
        """
        NOTE: This is the same signing key used to sign Algorand transactions.

        :return: private key used to sign messages
        """
        return SigningKey(bytes(self))

    @property
    def signing_address(self) -> SigningAddress:
        """
        Signing address is the same as the Algorand address, which corresponds to the Algorand account public key.

        :return: base32 encoded public signing address
        """
        return SigningAddress(
            Address(encode_address(bytes(self.signing_key.verify_key)))
        )

    def encrypt(
        self,
        msg: bytes,
        recipient: EncryptionAddress | None = None,
    ) -> bytes:
        """
        Encrypts a message that can only be decrypted by the recipient's private key.

        :param msg: message to encrypt
        :param recipient: if None, then recipient is set to self
        """
        encryption_address = recipient if recipient else self.encryption_address
        return Box(
            self,
            encryption_address.to_public_key(),
        ).encrypt(msg)

    def decrypt(
        self,
        msg: bytes,
        sender: EncryptionAddress | None = None,
    ) -> bytes:
        """
        Decrypts a message that was encrypted by the sender.

        :param sender: if None, then sender is set to self
        """
        encryption_address = sender if sender else self.encryption_address
        return Box(
            self,
            encryption_address.to_public_key(),
        ).decrypt(
            ciphertext=msg[Box.NONCE_SIZE :],
            nonce=msg[: Box.NONCE_SIZE],
        )

    def sign(self, msg: bytes) -> SignedMessage:
        """
        Signs the message.
        """
        return self.signing_key.sign(msg)

    def sign_transactions(
        self,
        txn_group: list[transaction.Transaction],
        indexes: list[int],
    ) -> list[GenericSignedTransaction]:
        stxns = []
        for i in indexes:
            stxn = txn_group[i].sign(
                base64.b64encode(
                    bytes(self) + bytes(self.signing_key.verify_key)
                ).decode()
            )
            stxns.append(stxn)
        return stxns
