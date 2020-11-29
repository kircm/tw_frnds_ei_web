import logging

from sqlalchemy.orm import session as orm_session

from .models import TaskStatus
from .models import TfeiTask

logger = logging.getLogger(__name__)


def handle_incomplete_tasks(db_session_maker):
    try:
        logger.info("Opening DB session")
        db_sess: orm_session = db_session_maker()

        num_tasks_incomplete = TfeiTask.count_incomplete(db_sess)

        if num_tasks_incomplete:
            logger.info(f"There are incomplete tasks from previous process: {num_tasks_incomplete}")
            handle_running(db_sess)
            handle_pending(db_sess)

    finally:
        db_sess.close()
        logger.info(f"Closed DB session")


def handle_running(db_sess):
    running_tasks = TfeiTask.get_running(db_sess)

    for running in running_tasks:
        logger.info(f"Setting task id {running.id} with status: RUNNING to status: PENDING")
        running.set_status_to(db_sess, TaskStatus.PENDING)


def handle_pending(db_sess):
    pending_tasks = TfeiTask.get_pending(db_sess)

    for pending in pending_tasks:
        logger.info(f"Setting task id {pending.id} with status: PENDING to status: CREATED")
        pending.set_status_to(db_sess, TaskStatus.CREATED)
