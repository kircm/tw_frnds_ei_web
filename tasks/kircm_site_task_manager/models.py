from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, func
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

TaskType = Enum('TaskType', 'IMPORT EXPORT')
TaskStatus = Enum('TaskStatus', 'CREATED APP_ERROR PENDING RUNNING FINISHED')


class TfeiTask(Base):
    __tablename__ = 'tfei_task'

    id = Column(Integer(), primary_key=True)
    tw_screen_name_for_task = Column(String(30))
    task_type = Column(String(20))
    task_status = Column(String(20))
    task_par_tw_id = Column(BigInteger)
    task_par_f_name = Column(String(100))
    pending_at = Column(DateTime)
    running_at = Column(DateTime)
    finished_at = Column(DateTime)
    finished_ok = Column(Boolean)
    finished_details = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    tw_user_id = Column(BigInteger, ForeignKey('tfei_twuser.tw_id'))
    tw_user = relationship("TfeiTwUser", back_populates="tfei_tasks")

    def __str__(self):
        return f"{self.id} - {self.tw_user} - {self.task_type} - {self.task_status} - updated-at: {self.updated_at}"

    def set_status_to(self, db_session, task_status):
        self.task_status = task_status.name
        self.updated_at = datetime.now()
        db_session.commit()

    # TODO: Move fetching of tasks to custom model manager?

    @staticmethod
    def get_by_id(db_sess, task_id):
        task = db_sess.query(TfeiTask).get(task_id)
        db_sess.commit()
        return task

    @staticmethod
    def created():
        return TfeiTask.task_status == TaskStatus.CREATED.name

    @staticmethod
    def pending():
        return TfeiTask.task_status == TaskStatus.PENDING.name

    @staticmethod
    def get_created(db_session):
        created = db_session.query(TfeiTask).filter(TfeiTask.created())
        db_session.commit()
        return created

    @staticmethod
    def get_pending(db_session):
        pending = db_session.query(TfeiTask).filter(TfeiTask.pending())
        db_session.commit()
        return pending

    @staticmethod
    def count_crated(db_session):
        count = db_session.query(func.count(TfeiTask.id)) \
            .filter(TfeiTask.task_status == TaskStatus.CREATED.name) \
            .scalar()
        db_session.commit()
        return count

    @staticmethod
    def count_crated_or_pending(db_session):
        count = db_session.query(func.count(TfeiTask.id)) \
            .filter(TfeiTask.task_status.in_([TaskStatus.CREATED.name, TaskStatus.PENDING.name])) \
            .scalar()
        db_session.commit()
        return count


class TfeiTwUser(Base):
    __tablename__ = 'tfei_twuser'

    tw_id = Column(BigInteger, primary_key=True)
    tw_screen_name = Column(String(30))
    tw_token = Column(String(100))
    tw_token_sec = Column(String(100))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    tfei_tasks = relationship("TfeiTask", back_populates="tw_user", lazy="dynamic")

    def __str__(self):
        return f"{self.tw_screen_name}({self.tw_id})"
