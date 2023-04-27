import logging
import re
import unittest
from logging import NOTSET, Handler, LogRecord, StreamHandler

from oysterpack.core.logging import configure_logging


class LogHandler(Handler):
    def __init__(self, level: int | str = NOTSET):
        super().__init__(level)
        self.records: list[LogRecord] = []

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)


logger = logging.getLogger(__name__)


class LoggingTestCase(unittest.TestCase):
    def test_configure_logging(self) -> None:
        # store current root logger config, which will be used to reset root logger when the test completes
        root_log_level = logging.root.level
        root_handlers = logging.root.handlers
        # clear handlers
        logging.root.handlers = []
        try:
            log_handler = LogHandler()
            configure_logging(handlers=[log_handler, StreamHandler()])
            self.assertEqual(logging.WARNING, logging.root.level)
            logger.warning("warning message")
            logger.info("info message")
            self.assertEqual(1, len(log_handler.records))
            # check the log record format
            match = re.match(
                rf"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d \[WARNING] \[{__name__}] warning message",
                log_handler.format(log_handler.records[0]),
            )
            self.assertIsNotNone(match)

            with self.subTest("set default log level to debug"):
                log_handler = LogHandler()
                configure_logging(
                    level=logging.DEBUG, handlers=[log_handler, StreamHandler()]
                )
                self.assertEqual(logging.DEBUG, logging.root.level)
                logger.warning("warning message")
                logger.info("info message")
                logger.debug("debug message")
                self.assertEqual(3, len(log_handler.records))

            configure_logging()
            self.assertEqual(logging.WARNING, logging.root.level)

        finally:
            # reset log level
            logging.root.setLevel(root_log_level)
            logging.root.handlers = root_handlers


if __name__ == "__main__":
    unittest.main()
