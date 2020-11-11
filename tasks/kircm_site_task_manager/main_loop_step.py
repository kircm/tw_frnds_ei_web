import logging
from collections import Sequence

from sqlalchemy.orm import session as orm_session
from sqlalchemy.orm import sessionmaker

from .models import TfeiTask
from .models import TfeiTwUser

logger = logging.getLogger(__name__)


def run_main_loop_step(db_engine):
    db_session: orm_session = sessionmaker(bind=db_engine)()

    print("\nTasks with CREATED status:\n")
    tasks_created: Sequence[TfeiTask] = TfeiTask.get_created(db_session)
    for t in tasks_created:
        print(t)
        print(f"  -> Task belongs to user: {t.tw_user}")

    print("\n-----")
    print("\nAll users and their tasks with CREATED status:")
    users: Sequence[TfeiTwUser] = db_session.query(TfeiTwUser)
    for u in users:
        print(u)
        user_tasks = u.tfei_tasks.filter(TfeiTask.created())

        print("  -> User has CREATED tasks:") if user_tasks.count() > 0 else print("  -> User has no CREATED tasks")

        for t in user_tasks:
            print(f"       {t}")
        print("\n")

    orm_session.close_all_sessions()

    # ----
    # TODO
    # ----
    # pull all CREATED tasks  into a list
    # update tasks status to PENDING

    # create thread pool executor
    # submit tasks ,  update task status to RUNNING
    # capture futures

    # monitor the tasks / futures

    # capture results - save them
    # update status to finished + finished details
    # ----

    # catch all exce to update task statuses to finished/NOK when there is a problem
    # if taks manager exits, all tasks are terminated?

    print("\n=====> All tasks finished.\n")
