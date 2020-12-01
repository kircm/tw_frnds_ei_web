import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config_env import MYSQL_DB_HOST
from .config_env import MYSQL_DB_PASSWORD
from .config_log import LOG_LEVEL
from .find_module_tw_frnds_ei import import_module_tw_frnds_ei
from .incomplete_tasks import handle_incomplete_tasks
from .main_loop_step import run_main_loop_step
from .task_monitor import TaskMonitor

logger = logging.getLogger(__name__)
logger.info(f"Logging enabled. Logging level: {logging.getLevelName(LOG_LEVEL)}")

TIMEOUT = 7 * 24 * 60 * 60  # After 7 days exit the main program - it will be restarted by hosting provider
WAIT = 10  # Sleeping time for polling DB
MAX_WORKERS = 20  # Max number of concurrent runnig threads for tasks


class Main:
    def __init__(self):
        db_engine = Main.get_db_engine()
        self.start = -1
        self.session_maker = sessionmaker(bind=db_engine)
        self.task_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.task_monitor = TaskMonitor()

    def main(self):
        print("Main Start")
        logger.info("Main Started")
        self.start = int(time.time())

        try:

            # RUN
            self.run()

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
                               echo=False,
                               pool_size=4,  # we are limited by the MySQL configuration in PROD max_user_connections
                               max_overflow=0,
                               pool_recycle=280  # this is needed to avoid losing
                                                 # idle DB connections
                                                 # https://help.pythonanywhere.com/pages/UsingSQLAlchemywithMySQL/
                               )
        return engine

    def run(self):
        end = self.start + TIMEOUT
        condition = self.start < end

        # Detect and handle incomplete tasks
        # It may happen if the process dies
        handle_incomplete_tasks(self.session_maker)

        while condition:
            logger.info("Running MAIN loop step")

            # main loop step execution
            run_main_loop_step(self.session_maker, self.task_executor, self.task_monitor)

            logger.info("MAIN loop step has been run. Did we do any work?")
            logger.debug("Sleeping...")
            time.sleep(WAIT)

            # check for timeout
            now = int(time.time())
            condition = now < end
            if not condition:
                logger.info(f"MAIN loop: TIMEOUT of {TIMEOUT} seconds reached.")


if __name__.endswith("__main__"):
    import_module_tw_frnds_ei()
    logger.info("Found and imported module 'tw_frnds_ei' for twitter api related tasks")
    Main().main()
