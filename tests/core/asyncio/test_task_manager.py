import asyncio
import logging
import random
import re
import unittest
from logging import StreamHandler

from ulid import ULID

from oysterpack.core.asyncio import task_manager
from oysterpack.core.logging import configure_logging
from tests import LogRecordCollection


async def foo() -> int:
    await asyncio.sleep(0)
    return random.randint(1, 1000)


class TaskManagerTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.root_log_level = logging.root.level
        self.root_handlers = logging.root.handlers
        self.log_records = LogRecordCollection()

        configure_logging(
            level=logging.DEBUG,
            handlers=[
                self.log_records,
                StreamHandler(),
            ],
        )

    def tearDown(self) -> None:
        # reset log level
        logging.root.setLevel(self.root_log_level)
        logging.root.handlers = self.root_handlers

    async def test_schedule(self) -> None:
        task_1 = task_manager.schedule(foo.__qualname__, foo())
        task_2 = task_manager.schedule(foo.__qualname__, foo())

        # debug log records should have been logged
        self.assertEqual(2, len(self.log_records.records))
        self.assertTrue(
            any(
                f"schedule({task_1.get_name()})" == record.getMessage()
                for record in self.log_records.records
            )
        )
        self.assertTrue(
            any(
                f"schedule({task_2.get_name()})" == record.getMessage()
                for record in self.log_records.records
            )
        )
        self.assertTrue(
            all(record.levelno == logging.DEBUG for record in self.log_records.records)
        )

        # check Task name pattern: TaskURI/ULID
        self.assertIsNotNone(
            re.match(rf"{foo.__qualname__}/\w{{26}}", task_1.get_name())
        )
        # Task names should be unique
        self.assertNotEqual(task_1.get_name(), task_2.get_name())

        # verify task references are saved
        self.assertTrue(task_manager.contains_task(task_1))
        self.assertTrue(task_manager.contains_task(task_2))

        task_1.cancel()
        await task_2

        # once tasks are done then their references should be discarded
        await asyncio.sleep(0)
        self.assertFalse(task_manager.contains_task(task_1))
        self.assertFalse(task_manager.contains_task(task_2))

        # debug log records should have been logged
        self.assertEqual(4, len(self.log_records.records))
        self.assertTrue(
            any(
                f"cancelled({task_1.get_name()})" == record.getMessage()
                for record in self.log_records.records
            )
        )
        self.assertTrue(
            any(
                f"done({task_2.get_name()})" == record.getMessage()
                for record in self.log_records.records
            )
        )

    async def test_task_uris(self) -> None:
        for _ in range(3):
            task_manager.schedule("foo", foo())
        for _ in range(4):
            task_manager.schedule("bar", foo())

        task_uris = task_manager.task_uris()
        self.assertIn("foo", task_uris)
        self.assertIn("bar", task_uris)
        self.assertNotIn(str(ULID()), task_uris)

    async def test_scheduled_task_counts(self) -> None:
        foo_tasks = [task_manager.schedule("foo", foo()) for _ in range(3)]
        bar_tasks = [task_manager.schedule("bar", foo()) for _ in range(4)]

        with self.subTest("when tasks have been scheduled"):
            task_counts = task_manager.scheduled_task_counts()
            self.assertEqual(len(foo_tasks), task_counts["foo"])
            self.assertEqual(len(bar_tasks), task_counts["bar"])

        with self.subTest("when all tasks have been completed"):
            await asyncio.gather(*foo_tasks, *bar_tasks)
            await asyncio.sleep(0)
            self.assertEqual(0, len(task_manager.scheduled_task_counts()))

    async def test_schedule_blocking_io_task(self) -> None:
        logger = logging.getLogger(__name__)
        await task_manager.schedule_blocking_io_task(logger.warning, "hello")

        def add(x: int, y: int) -> int:
            logger.info("%d + %d = %d", x, y, x + y)
            return x + y

        self.assertEqual(3, await task_manager.schedule_blocking_io_task(add, 1, 2))

    async def test_schedule_cpu_bound_task(self) -> None:
        rand_num = await task_manager.schedule_cpu_bound_task(random.randint, 1, 1000)
        self.assertTrue(1 <= rand_num <= 1000)


if __name__ == "__main__":
    unittest.main()
