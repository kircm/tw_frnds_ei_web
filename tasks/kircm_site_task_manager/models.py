from enum import Enum

from sqlalchemy import BigInteger
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


class TfeiTask(Base):
    __tablename__ = 'tfei_task'

    TaskType = Enum('TaskType', 'IMPORT EXPORT')
    TaskStatus = Enum('TaskStatus', 'CREATED PENDING RUNNING FINISHED')

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
        return f"{self.task_type} - {self.tw_user} - {self.task_status} - updated-at: {self.updated_at}"

    @staticmethod
    def created():
        return TfeiTask.task_status == TfeiTask.TaskStatus.CREATED.name

    @staticmethod
    def get_created(db_session):
        return db_session.query(TfeiTask).filter(TfeiTask.created())


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
