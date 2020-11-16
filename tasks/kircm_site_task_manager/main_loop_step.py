import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor

from sqlalchemy.orm import session as orm_session

from .models import TaskStatus
from .models import TfeiTask
from .task_monitor import ExistingTaskForUser
from .task_monitor import TaskMonitor
from .task_thread import task_thread

logger = logging.getLogger(__name__)

MAX_WORKERS = 7
WAIT_SECS = 10


def run_main_loop_step(db_session_maker):
    try:
        logger.info("Opening DB session")
        db_sess: orm_session = db_session_maker()
        executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

        num_tasks_created = TfeiTask.count_crated(db_sess)
        logger.info(f"Initial number of tasks with CREATED status: {num_tasks_created}")

        f_monitor = False
        task_monitor = None
        if num_tasks_created:
            logger.info(f"We have work to do. Num tasks with CREATED status: {num_tasks_created}")
            task_monitor = TaskMonitor()
            logger.info("Created task futures monitor")
            logger.info("Picking FIRST task for the new monitor...")
            pick_created(db_session_maker, db_sess, executor, task_monitor)
            f_monitor = executor.submit(task_monitor.monitor)
            logger.info("FIRST task picked and monitor is now running")

        while f_monitor:
            num_tasks_created_or_pending = TfeiTask.count_crated_or_pending(db_sess)
            logger.info("Monitor future is alive and we have this number of CREATED/PENDING tasks in "
                        f"DB: {num_tasks_created_or_pending}")

            while num_tasks_created_or_pending:
                # We need to keep looping if any task is in CREATED or PENDING status
                # We need to keep monitor ALIVE and it may be the case that a task
                # has been set to PENDING in DB but hasn't been added to the monitor yet
                # Eventually, it will be added to the monitor and eventually task will be set
                # to RUNNING by the task thread
                logger.info("Picking potentially existing CREATED task")
                pick_created(db_session_maker, db_sess, executor, task_monitor)

                num_tasks_created_or_pending = TfeiTask.count_crated_or_pending(db_sess)
                logger.info("Picked potentially existing CREATED task. We have now this number of CREATED/PENDING "
                            f"tasks in DB: {num_tasks_created_or_pending}")
                logger.info("Breathing...")
                time.sleep(WAIT_SECS)

            logger.info("There seems to be no more tasks to pick from DB")
            logger.info("Giving a break to the task futures monitor...")
            # No immediate tasks to pick (or is there??) - taking a break anyway
            time.sleep(WAIT_SECS)

            if f_monitor.done():
                logger.info(f"Monitor is Done. Actual state: {f_monitor}")
                f_monitor = False
                logger.info(f"About to leave MAIN loop step..")

        logger.info("Leaving MAIN loop step. We are done for now. Releasing DB Session.")

    except ExistingTaskForUser:
        # for now we accept that situation
        logger.warning("EXCEPTION EXISTING TASK FOR USER")

    finally:
        # Unconditionally close all DB connections
        orm_session.close_all_sessions()
        logger.info(f"Closed all DB sessions")


def pick_created(db_session_maker, db_sess, executor, monitor):
    task_created = TfeiTask.get_created(db_sess).first()

    if task_created:
        logger.info(f"About to pick task with CREATED status: {task_created}")

        if monitor.exists_task_for_key(task_created):
            # this shouldn't happen - Application Error
            task_created.set_status_to(TaskStatus.APP_ERROR)
            raise ExistingTaskForUser()

        task_created.set_status_to(db_sess, TaskStatus.PENDING)
        logger.info(f"Set CREATED task to PENDING status: {task_created}")

        logger.info(f"Submitting task with id {task_created.id} to task thread...")
        pars = {'db_session_maker': db_session_maker, 'task_id': task_created.id}
        future = executor.submit(task_thread, pars)
        logger.info(f"Submitted task with id {task_created.id} to task thread")
        monitor.add_future(task_created, future)
        logger.info(f"Added task future with task id: {task_created.id} to task thread monitor")
