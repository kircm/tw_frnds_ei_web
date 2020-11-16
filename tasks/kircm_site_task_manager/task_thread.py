import logging
import random
import threading
import time

from sqlalchemy.orm import session as orm_session

from .models import TaskStatus
from .models import TfeiTask

logger = logging.getLogger(__name__)


def requires_db_conn_refresh(func):
    def wrapper(*args, **kwargs):
        db_session_maker = kwargs['db_session_maker']
        db_sess = None

        try:
            logger.debug(f"Opening DB session")
            db_sess: orm_session = db_session_maker()
            # passing db session to wrapped function
            kwargs.update({'db_sess': db_sess})

            result = func(*args, **kwargs)

            db_sess.close()
            logger.debug(f"Closed DB session")

            return result

        except Exception as e:
            logger.error(e)
            raise e

        finally:
            db_sess.close()

    return wrapper


@requires_db_conn_refresh
def pick_pending_set_running(task_id, **kwargs):
    db_sess = kwargs['db_sess']

    pending_task = TfeiTask.get_by_id(db_sess, task_id)
    logger.info(f"Retrieved PENDING task: {task_id} - {pending_task}")

    # purposedly delaying setting to RUNNING status for preliminary testing for now
    time.sleep(random.randrange(8, 20))

    pending_task.set_status_to(db_sess, TaskStatus.RUNNING)
    logger.info(f"Set task to RUNNING status: {task_id} - {pending_task}")
    return pending_task


@requires_db_conn_refresh
def refresh_task_with_id(task_id, **kwargs):
    db_sess = kwargs['db_sess']
    time_to_finish = kwargs['time_to_finish']
    now = int(time.time())
    my_task = TfeiTask.get_by_id(db_sess, task_id)
    logger.info(f"Still working on task {task_id} with status {my_task.task_status} "
                f"and type {my_task.task_type} for user: {my_task.tw_user}... Still {time_to_finish - now} secs to go")

    return my_task


@requires_db_conn_refresh
def retrieve_running_set_finished(task_id, **kwargs):
    db_sess = kwargs['db_sess']
    running_task = TfeiTask.get_by_id(db_sess, task_id)
    running_task.set_status_to(db_sess, TaskStatus.FINISHED)
    logger.info(f"Set task to FINISHED status: {task_id} - {running_task}")


def task_thread(pars):
    db_session_maker = pars['db_session_maker']
    task_id = pars['task_id']
    # Set thread name for logging - debugging
    threading.current_thread().name = f"TaskThread_T{task_id}"

    try:
        logger.info(f"Picked up task: {task_id}")

        running_task = pick_pending_set_running(task_id, db_session_maker=db_session_maker)

        logger.info(f"Working on: {task_id} - {running_task} .................")
        start = int(time.time())
        time_to_finish = start + random.randrange(300, 5000)
        hit_db_every = 30

        condition = start < time_to_finish
        while condition:
            time.sleep(hit_db_every)
            now = int(time.time())

            task = refresh_task_with_id(task_id, time_to_finish=time_to_finish, db_session_maker=db_session_maker)
            logger.debug(f"Refreshed task with id: {task.id}")

            condition = now < time_to_finish

        # we reached time to finish - The simulation for this task is finished
        logger.info(f"FINISHED task: {task_id}")
        retrieve_running_set_finished(task_id, db_session_maker=db_session_maker)

    except Exception as e:
        logger.error(e)
        raise e

    return 0
