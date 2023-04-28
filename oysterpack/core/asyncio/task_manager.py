"""
Used to schedule tasks as reliable “fire-and-forget” background tasks

- Task references are saved to avoid the task disappearing mid-execution.
- The event loop only keeps weak references to tasks.
- A task that isn't referenced elsewhere may get garbage collected at any time, even before it's done.
"""
import asyncio
import logging
from asyncio import Task
from collections.abc import Callable, Coroutine
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, TypeVar

from ulid import ULID

TaskURI = str

TaskName = str

__tasks: dict[TaskURI, set[Task]] = {}
__logger = logging.getLogger(__name__)
__thread_pool_executor = ThreadPoolExecutor()
__process_pool_executor = ProcessPoolExecutor()


def contains_task(task: Task) -> bool:
    task_name = task.get_name().split("/")[0]
    tasks = __tasks.get(task_name)
    return tasks is not None and task in tasks


def task_uris() -> set[TaskURI]:
    """
    :return: set of all TaskURI(s) that have been registered
    """
    return set(__tasks.keys())


def scheduled_task_counts() -> dict[TaskURI, int]:
    """
    Returns counts onlt for TaskURI(s) that have currently running tasks

    :return: number of tasks currently scheduled per TaskURI
    """
    return {
        task_uri: len(tasks) for (task_uri, tasks) in __tasks.items() if len(tasks) > 0
    }


def schedule(task_uri: TaskURI, coroutine: Coroutine) -> Task:
    """
    Schedules the specified coroutine as a task with the event loop.

    Tasks are scheduled using a standard naming convention: task_uri/ULID
    - this enables the types of tasks that have been scheduled to be tracked

    Debug Logs
    ----------
    - when task is scheduled and when task is done

    :param task_uri: TaskURI
    :param coroutine: Coroutine
    :return: Task
    """
    task = asyncio.create_task(coroutine, name=f"{task_uri}/{str(ULID())}")
    __logger.debug("schedule(%s)", task.get_name())
    if task_uri in __tasks:
        __tasks[task_uri].add(task)
    else:
        __tasks[task_uri] = {task}

    def remove_task(task: Task) -> None:
        if task.cancelled():
            __logger.debug("cancelled(%s)", task.get_name())
        else:
            __logger.debug("done(%s)", task.get_name())

        return __tasks[task_uri].remove(task)

    task.add_done_callback(remove_task)

    return task


_T = TypeVar("_T")


async def schedule_blocking_io_task(func: Callable[..., _T], *args: Any) -> _T:
    """
    Runs the function using a ThreadPoolExecutor
    """
    return await asyncio.get_running_loop().run_in_executor(
        __thread_pool_executor, func, *args
    )


async def schedule_cpu_bound_task(func: Callable[..., _T], *args: Any) -> _T:
    """
    Runs the function using a ProcessPoolExecutor

    NOTES
    -----
    All arg and return types must be able to be marshalled, i.e. pickled, across processes
    """
    return await asyncio.get_running_loop().run_in_executor(
        __process_pool_executor, func, *args
    )
