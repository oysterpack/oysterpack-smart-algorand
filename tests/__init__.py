from logging import NOTSET, Handler, LogRecord


class LogRecordCollection(Handler):
    def __init__(self, level: int | str = NOTSET):
        super().__init__(level)
        self.records: list[LogRecord] = []

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)
