"""
Provides support for logging
"""

import logging
import time


def configure_logging(
    level: int = logging.WARNING,
    handlers: list[logging.Handler] | None = None,
) -> None:
    """
    Configures logging format and log level.

    :param level: default = WARNING
    :param handlers: optional list of Handler instances
    :return: None

    - log format: %(asctime)s [%(levelname)s] [%(name)s] %(message)s
    - timestamps are UTC
    - best practice is to retrieve a logger using the module's name:

    >>> configure_logging(level=logging.DEBUG)
    >>> logger = logging.getLogger('oysterpack.algorand')
    >>> logger.info('Algorand is the future of finance') # doctest: +SKIP
    2023-01-09 14:48:20,594 [INFO] [oysterpack.algorand] Algorand is the future of finance

    """
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        level=level,
        handlers=handlers,
        force=True,
    )
    logging.captureWarnings(capture=True)
