import asyncio
import random
import unittest

from oysterpack.core.ulid import HashableULID


class Foo:
    async def __call__(self) -> int:
        await asyncio.sleep(0)
        return random.randint(1, 100)

    @staticmethod
    def task_name() -> str:
        return Foo.__qualname__


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here

    def test_run_async_func(self):
        result = asyncio.run(Foo()())
        self.assertTrue(1 <= result <= 100)


class MyAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_task_name(self) -> None:
        async def foo() -> int:
            await asyncio.sleep(0)
            return random.randint(1, 100)

        task = asyncio.create_task(foo())
        print(task.get_name())

    async def test_task_name_callable(self) -> None:
        foo = Foo()
        task = asyncio.create_task(foo(), name=f"{Foo.task_name()}/{HashableULID()!s}")
        print(task.get_name())


if __name__ == "__main__":
    unittest.main()
