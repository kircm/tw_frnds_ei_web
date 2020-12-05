import logging
import random
import threading
import time

from sqlalchemy.orm import session as orm_session

from .exporter_task import exporter_task
from .importer_task import importer_task
from .models import TaskStatus
from .models import TaskType
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
    time.sleep(random.randrange(10, 40))

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
def retrieve_running_set_finished_info(task_id, ok, output, finished_details, **kwargs):
    db_sess = kwargs['db_sess']
    running_task = TfeiTask.get_by_id(db_sess, task_id)
    running_task.set_finished_info_to(db_sess, ok, output, finished_details)
    running_task.set_status_to(db_sess, TaskStatus.FINISHED)
    if ok:
        logger.info("Task finished OK!")
    else:
        logger.warning(f"Task finished NOT OK. Details about error: {finished_details}")

    logger.info(f"Set task to FINISHED status: {task_id} - {running_task}")


def do_task(task, **kwargs):
    db_session_maker = kwargs['db_session_maker']
    task_id = task.id
    user_token = task.tw_user.tw_token
    user_token_secret = task.tw_user.tw_token_sec

    if task.task_type == TaskType.EXPORT.name:
        export_for_user = task.task_par_tw_id
        if not export_for_user:
            raise RuntimeError(f"SystemError: Export task {task_id} doesn't have the tw user to export "
                               f"friends for configured!")
        ok, msg, file_name = exporter_task(user_token, user_token_secret, export_for_user)
        retrieve_running_set_finished_info(task_id, ok, file_name, msg, db_session_maker=db_session_maker)

    elif task.task_type == TaskType.IMPORT.name:
        csv_file_name = task.task_par_f_name
        if not csv_file_name:
            raise RuntimeError(f"SystemError: Import task {task_id} doesn't have the file name to import configured!")
        ok, msg, friendships_remaining = importer_task(user_token, user_token_secret, csv_file_name)
        retrieve_running_set_finished_info(task_id, ok, friendships_remaining, msg, db_session_maker=db_session_maker)

    else:
        raise NotImplementedError(f"Task type: {task.task_type} doesn't have an implementation")


def task_thread_fn(pars):
    db_session_maker = pars['db_session_maker']
    task_id = pars['task_id']
    # Set thread name for logging - debugging
    threading.current_thread().name = f"TaskThread_T{task_id}"

    try:
        logger.info(f"Picked up task: {task_id}")
        running_task = pick_pending_set_running(task_id, db_session_maker=db_session_maker)

        logger.info(f"Working on: {task_id} - {running_task} ...")
        do_task(running_task, db_session_maker=db_session_maker)
        logger.info(f"Done with: {task_id} - {running_task} ...")

    except Exception as e:
        logger.error(e)
        err_msg = f"Task thread for task {task_id} raised exception: {e}"
        retrieve_running_set_finished_info(task_id, False, None, err_msg, db_session_maker=db_session_maker)
        raise e

    return 0
