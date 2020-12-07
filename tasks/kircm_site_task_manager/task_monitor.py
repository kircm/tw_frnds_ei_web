import functools
import logging
import threading
import time

logger = logging.getLogger(__name__)


class TaskMonitor:
    __WAIT_SECS = 4

    def __init__(self):
        self.__TASK_FUTURES = {}
        self.__TASK_FUTURES_LOCK = threading.Lock()

    #
    # lock/release decorator
    #
    # noinspection PyMethodParameters
    def locks_task_futures_collection(func):
        """
        This decorator wraps functions that require a synchronous operation with task futures collection.

        """

        # noinspection PyTypeChecker, PyCallingNonCallable

        # For operations that need to be run within a mutex locking __TASK_FUTURES
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor_instance = args[0]
            monitor_lock = monitor_instance.__TASK_FUTURES_LOCK
            monitor_lock.acquire()
            result = func(*args, **kwargs)
            monitor_lock.release()
            return result

        return wrapper

    # noinspection PyArgumentList
    @locks_task_futures_collection
    def exists_task_for_key(self, task):
        # key = task.tw_user_id
        # We use task id as key for now
        key = task.id
        exists = key in self.__TASK_FUTURES
        if exists:
            logger.warning(f"Task for key: {key} already existing in task monitor!")
        return exists

    # noinspection PyArgumentList
    @locks_task_futures_collection
    def add_future(self, task, future):
        # key = task.tw_user_id
        # We use task id as key for now
        key = task.id
        logger.info(f"Adding future for task with key: {key}")
        self.__TASK_FUTURES[key] = future

    # noinspection PyArgumentList
    @locks_task_futures_collection
    def all_finished(self):
        logger.debug("All futures finished?")
        num_futures = len(self.__TASK_FUTURES) == 0
        logger.debug(f"Returning num_futures: {num_futures}")
        return num_futures

    # noinspection PyArgumentList
    @locks_task_futures_collection
    def num_unfinished(self):
        num_unfinished = len(self.__TASK_FUTURES)
        return num_unfinished

    # noinspection PyArgumentList
    @locks_task_futures_collection
    def __remove_finished_futures(self):
        # we need to lock access to the dict holding all
        # futures for tasks while we do a pass to
        # remove finished ones
        futures_to_check = iter(self.__TASK_FUTURES.items())
        f_item = next(futures_to_check, None)
        while f_item:
            if f_item[1].done():
                self.__TASK_FUTURES.pop(f_item[0])
                # we recreate iterator to refresh the current
                # state of task futures dict - as we have popped an item
                futures_to_check = iter(self.__TASK_FUTURES.items())
            f_item = next(futures_to_check, None)
        return len(self.__TASK_FUTURES)

    def monitor_fn(self):
        threading.current_thread().name = "TaskMonitor"
        logger.info(f"Starting monitoring on futures: {self.__TASK_FUTURES}")
        unfinished = self.num_unfinished()
        logger.info(f"Initial unfinished task futures: {unfinished}")

        while unfinished:
            logger.info(f"Current unfinished task futures: {unfinished}")
            unfinished = self.__remove_finished_futures()
            logger.debug(f"After sweeping current task futures we have now {unfinished}")

            # we've looped through the task futures and removed the ones that were finished
            # we want to have breathing time, no point in checking for task futures immediately
            time.sleep(self.__WAIT_SECS)
            # the main thread may have added task futures
            unfinished = self.num_unfinished()

        # All task futures finished - time to release resources
        logger.info(f"There are now {unfinished} task futures - EXITING MONITOR")
        return 0


class ExistingTaskForUser(Exception):
    pass
