import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from ulid import ULID

from oysterpack.apps.algo.app import App, AppConfig

sandbox_config = b"""
[algod]
token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
url="http://localhost:4001"

[kmd]
token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
url="http://localhost:4002"
"""


class AppConfigTestCase(unittest.TestCase):
    def test_from_config_file(self):
        with self.subTest("valid config format"):
            with NamedTemporaryFile() as config_file:
                config_file.write(
                    b"""
                [algod]
                token="aaa"
                url="http://localhost:4001"

                [kmd]
                token="bbb"
                url="http://localhost:4002"
                """
                )
                config_file.flush()
                app_config = AppConfig.from_config_file(Path(config_file.name))
                self.assertEqual("http://localhost:4001", app_config.algod_config.url)
                self.assertEqual(
                    "aaa",
                    app_config.algod_config.token,
                )
                self.assertEqual("http://localhost:4002", app_config.kmd_config.url)
                self.assertEqual(
                    "bbb",
                    app_config.kmd_config.token,
                )

        with self.subTest("empty config file"):
            with NamedTemporaryFile() as config_file:
                with self.assertRaises(KeyError) as err:
                    AppConfig.from_config_file(Path(config_file.name))
                self.assertEqual("'algod'", str(err.exception))

        with self.subTest("config file does not exist"):
            with self.assertRaises(FileNotFoundError):
                AppConfig.from_config_file(Path(str(ULID())))


class AppTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_check_connections(self):
        with self.subTest("valid config"):
            with NamedTemporaryFile() as config_file:
                config_file.write(sandbox_config)
                config_file.flush()
                app_config = AppConfig.from_config_file(Path(config_file.name))
                app = App(app_config)
                await app.check_connections()
                wallets = await app.list_wallets()
                self.assertTrue(len(wallets) > 0)

        with self.subTest("invalid algod config"):
            with NamedTemporaryFile() as config_file:
                config_file.write(
                    b"""
            [algod]
            token="INVALID_TOKEN"
            url="http://localhost:4001"

            [kmd]
            token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            url="http://localhost:4002"
            """
                )
                config_file.flush()
                app_config = AppConfig.from_config_file(Path(config_file.name))
                app = App(app_config)
                with self.assertRaises(AssertionError) as err:
                    await app.check_connections()
                self.assertEqual(
                    "Failed to connect to Algorand node", err.exception.args[0]
                )

        with self.subTest("invalid kmd config"):
            with NamedTemporaryFile() as config_file:
                config_file.write(
                    b"""
            [algod]
            token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            url="http://localhost:4001"

            [kmd]
            token="INVALID_TOKEN"
            url="http://localhost:4002"
            """
                )
                config_file.flush()
                app_config = AppConfig.from_config_file(Path(config_file.name))
                app = App(app_config)
                with self.assertRaises(AssertionError) as err:
                    await app.check_connections()
                self.assertEqual("Failed to connect to KMD node", err.exception.args[0])


if __name__ == "__main__":
    unittest.main()
