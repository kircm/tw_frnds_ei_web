import logging
from logging.handlers import RotatingFileHandler

from .config_env import DEBUG


class StripPackageFormatter(logging.Formatter):
    """
    This custom formatter strips out the package info.

    This task manager application has only one package. The package is used for
    documentation purposes. In all effects the modules belong to the one and only
    package which encapsulates the application. For logging though is inconvenient.
    """

    def __init__(self, log_format):
        super().__init__(log_format)

    def format(self, record):
        record.name = record.name.split(".")[-1]
        return super().format(record)


LOG_FORMAT = '%(asctime)s %(levelname)8s %(threadName)-20s %(name)15s - %(message)s'
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

root_logger = logging.root
root_logger.setLevel(LOG_LEVEL)

file_handler = RotatingFileHandler(filename="log.log",
                                   mode="a",
                                   encoding="UTF-8",
                                   maxBytes=10485760,  # 10MB
                                   backupCount=9)
file_handler.setFormatter(StripPackageFormatter(LOG_FORMAT))

root_logger.addHandler(file_handler)
