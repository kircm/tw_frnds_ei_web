import logging
import time

from sqlalchemy import create_engine

from .config_env import MYSQL_DB_HOST
from .config_env import MYSQL_DB_PASSWORD
from .config_log import LOG_LEVEL
from .main_loop_step import run_main_loop_step

logger = logging.getLogger(__name__)
logger.info(f"Logging enabled. Logging level: {logging.getLevelName(LOG_LEVEL)}")

TIMEOUT = 300
WAIT = 40


class Main:
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def main(self):
        print("Main Start")
        logger.info("Main Started")
        start = int(time.time())
        end = start + TIMEOUT
        condition = start < end

        try:
            while condition:

                # RUN
                run_main_loop_step(self.db_engine)

                # for now run one loop step
                # return
                # for now run one loop step

                time.sleep(WAIT)

                # check for timeout
                now = int(time.time())
                condition = now < end

        except Exception as e:
            logger.error(e)
            raise e
        except KeyboardInterrupt:
            logger.warning(KeyboardInterrupt.__name__)
        except SystemExit:
            logger.warning(SystemExit.__name__)
        finally:
            logger.info("Main Ended")
            print("Main End")

    @staticmethod
    def get_db_engine():
        engine = create_engine(f"mysql://kircm:{MYSQL_DB_PASSWORD}@{MYSQL_DB_HOST}/kircm$kircm_db",
                               encoding='utf8',
                               echo=False)
        return engine


if __name__.endswith("__main__"):
    Main(Main.get_db_engine()).main()
