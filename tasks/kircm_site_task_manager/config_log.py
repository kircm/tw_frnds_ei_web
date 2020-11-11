import logging
from .config_env import DEBUG

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s - %(message)s'
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(filename="log.log",
                    filemode="a",
                    format=LOG_FORMAT,
                    level=LOG_LEVEL)
