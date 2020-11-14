import logging
import random
import time

from sqlalchemy.orm import session as orm_session

from .models import TaskStatus
from .models import TfeiTask

logger = logging.getLogger(__name__)


def task_thread(pars):
    db_session_maker = pars['db_session_maker']
    task_id = pars['task_id']

    # Open a new connection to DB
    logger.info(f"Opening DB session")
    db_sess: orm_session = db_session_maker()

    try:
        logger.info(f"Picked up task: {task_id}")
        pending_task = TfeiTask.get_by_id(db_sess, task_id)
        logger.info(f"Retrieved PENDING task: {task_id} - {pending_task}")

        # purposedly delaying setting to RUNNING status for preliminary testing for now
        time.sleep(random.randrange(2, 8))

        pending_task.set_status_to(db_sess, TaskStatus.RUNNING)
        logger.info(f"Set task to RUNNING status: {task_id} - {pending_task}")

        running_task = pending_task  # just for clarity
        logger.info(f"Working on: {task_id} - {running_task} .................")
        time.sleep(random.randrange(300, 5000))

        logger.info(f"FINISHED task: {task_id} - {running_task}")
        running_task.set_status_to(db_sess, TaskStatus.FINISHED)
        logger.info(f"Set task to FINISHED status: {task_id} - {running_task}")

    finally:
        db_sess.close()
        logger.info(f"Closed DB session")

    return 0
