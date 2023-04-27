import unittest

from oysterpack.core.ulid import HashableULID


class HashableULIDTestCase(unittest.TestCase):
    def test_hashing(self) -> None:
        with self.subTest("HashableULID can be used as keys in a dict"):
            data: dict[HashableULID, str] = {}

            keys = [HashableULID() for _ in range(10)]
            for key in keys:
                data[key] = str(key)

            self.assertEqual(10, len(data))

            for key in keys:
                self.assertEqual(key, HashableULID.from_str(data[key]))


if __name__ == "__main__":
    unittest.main()
