from application.utility.database_query import select_from_db, update_status_in_db
from application.utility.models_process import (ExecuteTask, task_from_dict, ExecuteTaskControl, ExecuteCheck,
                                                ExecuteTaskRead)
from application.utility.launch import do_execute_task
from application.utility.mail import Email
from threading import Thread
import sched
from time import time, sleep
from typing import Union
import logging

SETTING_INTERVAL = 60 * 30


class TaskingProcess:
    running_task: ExecuteTask
    setting_count: int = 0
    sent_report: bool = False

    def email_report(self):
        _status = self.running_task.status
        if not self.sent_report:
            _message = f'{self.running_task.container} {_status}'
            Email().send(message=_message, email=self.running_task.email)
            self.sent_report = True

    def error_task(self):
        logging.info('task error')
        self.running_task.status = 'error'
        update_status_in_db(self.running_task)
        self.email_report()

    def check_for_api_failure(self):
        logging.info('checking for api execution failure')
        if self.setting_count == 2:
            _control_ids = select_from_db(
                ExecuteTaskControl.__tablename__,
                columns=['control_id'],
                where_condition={'task_id': self.running_task.id}, keys=False)
            logging.info(f'executed controls {len(_control_ids)}')
            _checks = [ExecuteCheck(**c) for c in select_from_db(
                ExecuteCheck.__tablename__,
                columns=['id'],
                where_condition={'container': self.running_task.container}, keys=True)]
            _checks = [c for c in _checks if c.timestamp > self.running_task.start]
            _read_ids = select_from_db(
                ExecuteTaskRead.__tablename__,
                columns=['read_id'],
                where_condition={'task_id': self.running_task.id}, keys=False)
            if not _read_ids or (not _control_ids and not _checks):
                logging.warning('api execution failure')
                self.error_task()


class TaskingScheduling(TaskingProcess):

    def update_task_status(self):
        logging.info('retrieving task at hand')
        select_status = select_from_db(
                table_name=ExecuteTask.__tablename__,
                columns=['id'],
                where_condition={'id': self.running_task.id}, keys=False)
        if not select_status or select_status == 'cancelled':
            exit()
        elif select_status in ('ended', 'error'):
            self.running_task.status = select_status
            self.email_report()
            exit()

    def schedule_execution(self):
        logging.info(f'scheduling task {self.running_task.container}')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(
            self.running_task.start, 0, do_execute_task, kwargs={'exec_task_id': self.running_task.id})
        scheduler.run()

    def task_schedule_process(self, execute_task: ExecuteTask):
        self.running_task = execute_task
        self.update_task_status()
        logging.info(f'task status {self.running_task.status}')
        if self.running_task.status == 'running':
            self.schedule_execution()
            if time() < self.running_task.start + self.running_task.duration*1.25:
                sleep(SETTING_INTERVAL)
                self.setting_count += 1
                logging.info(f'setting count {self.setting_count}')
                self.check_for_api_failure()
                self.task_schedule_process(self.running_task)
            else:
                self.error_task()


def thread_task(execute_task: ExecuteTask):
    logging.info(f'threading tasking api launch')
    thread = Thread(target=TaskingScheduling().task_schedule_process, args=[execute_task])
    thread.start()
