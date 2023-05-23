import unittest
from typing import Final, cast

from beaker import localnet
from click import BaseCommand
from click.testing import CliRunner
from ulid import ULID

from oysterpack.apps.algo.cli import cli

localnet_config = f"""
[algod]
token="{localnet.clients.DEFAULT_ALGOD_TOKEN}"
url="{localnet.clients.DEFAULT_ALGOD_ADDRESS}"

[kmd]
token="{localnet.kmd.DEFAULT_KMD_TOKEN}"
url="{localnet.kmd.DEFAULT_KMD_ADDRESS}"
""".encode()

ALGO_CONFIG_FILE = "algo.toml"


class CliTestCase(unittest.TestCase):
    def test_list_wallets(self):
        kmd = localnet.kmd.get_client()
        wallets = kmd.list_wallets()

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open(ALGO_CONFIG_FILE, "wb") as f:
                f.write(localnet_config)

            result = runner.invoke(
                cast(BaseCommand, cli),
                ["kmd", "--config-file", ALGO_CONFIG_FILE, "list-wallets"],
            )
            self.assertEqual(0, result.exit_code)

            # wallets should be returned sorted by wallet name
            wallets = sorted(wallets, key=lambda wallet: wallet["name"])
            lines = result.output.split("\n")
            lines = lines[
                : len(lines) - 1
            ]  # remove last line, which will be an empty line
            for wallet, line in zip(wallets, lines, strict=True):
                self.assertTrue(wallet["name"] in line)

    # @unittest.skip("hangs")
    def test_create_wallet(self) -> None:
        wallet_name_prompt: Final[str] = "Wallet Name:"
        wallet_password_prompt: Final[str] = "Wallet Password:"
        confirmation_prompt: Final[str] = "Repeat for confirmation:"
        wallet_created_success_message: Final[str] = "Wallet was successfully created"

        kmd = localnet.kmd.get_client()

        runner = CliRunner()
        with self.subTest("create wallet"):
            with runner.isolated_filesystem():
                with open(ALGO_CONFIG_FILE, "wb") as f:
                    f.write(localnet_config)

                wallet_name = str(ULID())
                wallet_password = str(ULID())

                result = runner.invoke(
                    cast(BaseCommand, cli),
                    ["kmd", "--config-file", ALGO_CONFIG_FILE, "create-wallet"],
                    input=f"{wallet_name}\n{wallet_password}\n{wallet_password}\n",
                )
                self.assertEqual(0, result.exit_code)

                self.assertTrue(
                    any(wallet["name"] == wallet_name for wallet in kmd.list_wallets())
                )

                lines = result.output.split("\n")
                self.assertTrue(lines[0].startswith(wallet_name_prompt))
                self.assertTrue(lines[1].startswith(wallet_password_prompt))
                self.assertTrue(lines[2].startswith(confirmation_prompt))
                self.assertEqual(wallet_created_success_message, lines[3])

        with self.subTest("create wallet using name that already exists"):
            with runner.isolated_filesystem():
                with open(ALGO_CONFIG_FILE, "wb") as f:
                    f.write(localnet_config)

                preexisting_wallet_name = wallet_name
                wallet_name = str(ULID())
                wallet_password = str(ULID())

                result = runner.invoke(
                    cast(BaseCommand, cli),
                    ["kmd", "--config-file", ALGO_CONFIG_FILE, "create-wallet"],
                    input=f"{preexisting_wallet_name}\n{wallet_name}\n{wallet_password}\n{wallet_password}\n",
                )
                self.assertEqual(0, result.exit_code)

                self.assertTrue(
                    any(wallet["name"] == wallet_name for wallet in kmd.list_wallets())
                )

                lines = result.output.split("\n")
                self.assertTrue(lines[0].startswith(wallet_name_prompt))
                self.assertEqual(
                    "Error: wallet with the same name already exists", lines[1]
                )
                self.assertTrue(lines[2].startswith(wallet_name_prompt))
                self.assertTrue(lines[3].startswith("Wallet Password:"))
                self.assertTrue(lines[4].startswith(confirmation_prompt))
                self.assertEqual(wallet_created_success_message, lines[5])

        with self.subTest(
            "create wallet using name that already exists, then blank name"
        ):
            with runner.isolated_filesystem():
                with open(ALGO_CONFIG_FILE, "wb") as f:
                    f.write(localnet_config)

                preexisting_wallet_name = wallet_name
                blank_name = " "
                wallet_name = str(ULID())
                wallet_password = str(ULID())

                result = runner.invoke(
                    cast(BaseCommand, cli),
                    ["kmd", "--config-file", ALGO_CONFIG_FILE, "create-wallet"],
                    input=f"{preexisting_wallet_name}\n{blank_name}\n{wallet_name}\n{wallet_password}\n{wallet_password}\n",
                )
                self.assertEqual(0, result.exit_code)

                self.assertTrue(
                    any(wallet["name"] == wallet_name for wallet in kmd.list_wallets())
                )

                lines = result.output.split("\n")
                self.assertTrue(lines[0].startswith(wallet_name_prompt))
                self.assertEqual(
                    "Error: wallet with the same name already exists", lines[1]
                )
                self.assertTrue(lines[2].startswith(wallet_name_prompt))
                self.assertEqual("Error: wallet name cannot be blank", lines[3])
                self.assertTrue(lines[4].startswith(wallet_name_prompt))
                self.assertTrue(lines[5].startswith(wallet_password_prompt))
                self.assertTrue(lines[6].startswith(confirmation_prompt))
                self.assertEqual(wallet_created_success_message, lines[7])

        with self.subTest("create wallet with blank name"):
            with runner.isolated_filesystem():
                with open(ALGO_CONFIG_FILE, "wb") as f:
                    f.write(localnet_config)

                wallet_name = str(ULID())
                wallet_password = str(ULID())

                result = runner.invoke(
                    cast(BaseCommand, cli),
                    ["kmd", "--config-file", ALGO_CONFIG_FILE, "create-wallet"],
                    input=f" \n{wallet_name}\n{wallet_password}\n{wallet_password}\n",
                )
                self.assertEqual(0, result.exit_code)

                self.assertTrue(
                    any(wallet["name"] == wallet_name for wallet in kmd.list_wallets())
                )

                lines = result.output.split("\n")

                self.assertTrue(lines[0].startswith(wallet_name_prompt))
                self.assertEqual("Error: wallet name cannot be blank", lines[1])
                self.assertTrue(lines[2].startswith(wallet_name_prompt))
                self.assertTrue(lines[3].startswith(wallet_password_prompt))
                self.assertTrue(lines[4].startswith(confirmation_prompt))
                self.assertEqual(wallet_created_success_message, lines[5])

        with self.subTest("create wallet with blank password"):
            with runner.isolated_filesystem():
                with open(ALGO_CONFIG_FILE, "wb") as f:
                    f.write(localnet_config)

                wallet_name = str(ULID())
                wallet_password = " "

                result = runner.invoke(
                    cast(BaseCommand, cli),
                    ["kmd", "--config-file", ALGO_CONFIG_FILE, "create-wallet"],
                    input=f"{wallet_name}\n{wallet_password}\n{wallet_password}\n",
                )
                self.assertNotEqual(result.exit_code, 0)

                lines = result.output.split("\n")
                self.assertEqual(
                    "Error: password cannot be blank", lines[len(lines) - 2]
                )


if __name__ == "__main__":
    unittest.main()
