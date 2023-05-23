import unittest
from typing import cast

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

    @unittest.skip("hangs")
    def test_create_wallet(self):
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
                    input=f"{wallet_name}\n{wallet_password}\n",
                )
                self.assertEqual(0, result.exit_code)

                self.assertTrue(
                    any(wallet["name"] == wallet_name for wallet in kmd.list_wallets())
                )


if __name__ == "__main__":
    unittest.main()
