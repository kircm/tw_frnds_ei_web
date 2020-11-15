import logging
import threading
import time

logger = logging.getLogger(__name__)


class TaskMonitor:
    __WAIT_SECS = 4

    def __init__(self):
        self.__TASK_FUTURES = {}
        self.__TASK_FUTURES_LOCK = threading.Lock()

    # TODO: Use locking decorator for synchronous methods

    def exists_task_for_key(self, task):
        # key = task.tw_user_id
        # We use task id as key for now
        key = task.id

        self.__TASK_FUTURES_LOCK.acquire()
        exists = key in self.__TASK_FUTURES
        self.__TASK_FUTURES_LOCK.release()

        if exists:
            logger.warning(f"Task for key: {key} already existing in task monitor!")
        return exists

    def add_future(self, task, future):
        # key = task.tw_user_id
        # We use task id as key for now
        key = task.id

        logger.info(f"Adding future for task with key: {key}")
        self.__TASK_FUTURES_LOCK.acquire()
        self.__TASK_FUTURES[key] = future
        self.__TASK_FUTURES_LOCK.release()

    def all_finished(self):
        logger.debug("All futures finished?")
        self.__TASK_FUTURES_LOCK.acquire()
        num_futures = len(self.__TASK_FUTURES) == 0
        self.__TASK_FUTURES_LOCK.release()
        logger.debug(f"Returning num_futures: {num_futures}")
        return num_futures

    def num_unfinished(self):
        logger.debug("num unfinished?")
        self.__TASK_FUTURES_LOCK.acquire()
        num_unfinished = len(self.__TASK_FUTURES)
        self.__TASK_FUTURES_LOCK.release()
        logger.debug(f"Returning num unfinished: {num_unfinished}")
        return num_unfinished

    def monitor(self):
        threading.current_thread().name = "TaskMonitor"
        logger.info(f"Starting monitoring on futures: {self.__TASK_FUTURES}")
        unfinished = self.num_unfinished()
        logger.info(f"Initial unfinished task futures: {unfinished}")

        while unfinished:
            logger.info(f"while unfinished loop: {unfinished} tasks")

            # we need to lock access to the dict holding all
            # futures for tasks while we do a pass to
            # remove finished ones
            self.__TASK_FUTURES_LOCK.acquire()
            unfinished = self.__remove_finished_futures()
            self.__TASK_FUTURES_LOCK.release()
            logger.info(f"After sweeping current task futures we have now {unfinished}")

            # we've looped through the task futures and removed the ones that were finished
            # we want to have breathing time, no point in checking for task futures immediately
            time.sleep(self.__WAIT_SECS)
            # the main thread may have added task futures
            unfinished = self.num_unfinished()

        # All task futures finished - time to release resources
        logger.info(f"There are now {unfinished} task futures - EXITING MONITOR")
        return 0

    # Needs to be run within a mutex locking __TASK_FUTURES
    def __remove_finished_futures(self):
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


class ExistingTaskForUser(Exception):
    pass
