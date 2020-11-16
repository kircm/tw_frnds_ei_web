import logging
import random
import threading
import time

from sqlalchemy.orm import session as orm_session

from .models import TaskStatus
from .models import TfeiTask

logger = logging.getLogger(__name__)


def task_thread(pars):
    db_session_maker = pars['db_session_maker']
    task_id = pars['task_id']
    threading.current_thread().name = f"TaskThread_T{task_id}"

    # Open a new connection to DB
    logger.info(f"Opening DB session")
    db_sess: orm_session = db_session_maker()

    try:
        logger.info(f"Picked up task: {task_id}")
        pending_task = TfeiTask.get_by_id(db_sess, task_id)
        logger.info(f"Retrieved PENDING task: {task_id} - {pending_task}")

        # purposedly delaying setting to RUNNING status for preliminary testing for now
        time.sleep(random.randrange(8, 20))

        pending_task.set_status_to(db_sess, TaskStatus.RUNNING)
        logger.info(f"Set task to RUNNING status: {task_id} - {pending_task}")

        running_task = pending_task  # just for clarity
        logger.info(f"Working on: {task_id} - {running_task} .................")

        start = int(time.time())
        time_to_finish = start + random.randrange(300, 5000)
        hit_db_every = 30

        condition = start < time_to_finish
        while condition:
            time.sleep(hit_db_every)
            now = int(time.time())
            my_task = TfeiTask.get_by_id(db_sess, task_id)
            logger.info(f"Still working on task {task_id} with status {my_task.task_status} "
                        f"and type {my_task.task_type}... Still {time_to_finish - now} secs to go")
            condition = now < time_to_finish

        logger.info(f"FINISHED task: {task_id}")
        running_task.set_status_to(db_sess, TaskStatus.FINISHED)
        logger.info(f"Set task to FINISHED status: {task_id} - {running_task}")

    except Exception as e:
        logger.error(e)
        raise e

    finally:
        db_sess.close()
        logger.info(f"Closed DB session")

    return 0
