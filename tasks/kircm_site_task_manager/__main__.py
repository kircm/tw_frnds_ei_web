import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config_env import MYSQL_DB_HOST
from .config_env import MYSQL_DB_PASSWORD
from .config_log import LOG_LEVEL
from .main_loop_step import run_main_loop_step

logger = logging.getLogger(__name__)
logger.info(f"Logging enabled. Logging level: {logging.getLevelName(LOG_LEVEL)}")

TIMEOUT = 3000
WAIT = 4


class Main:
    def __init__(self, db_engine):
        self.session_maker = sessionmaker(bind=db_engine)

    def main(self):
        print("Main Start")
        logger.info("Main Started")
        start = int(time.time())
        end = start + TIMEOUT
        condition = start < end

        try:
            while condition:
                logger.info("Running MAIN loop step")

                # RUN
                run_main_loop_step(self.session_maker)

                logger.info("MAIN loop step has been run. Did we do any work?")
                logger.info("Sleeping...")
                time.sleep(WAIT)

                # check for timeout
                now = int(time.time())
                condition = now < end
                if condition:
                    logger.info(f"MAIN loop: TIMEOUT of {TIMEOUT} seconds reached.")

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
