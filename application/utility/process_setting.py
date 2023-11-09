from application.utility.database_query import select_from_db, update_status_in_db
from application.utility.models_process import ExecuteSet, ExecuteSetControl
from application.utility.launch import api_execute_setting
from threading import Thread
import sched
from time import time, sleep
from typing import Union
import logging

RETRY = 4
SETTING_INTERVAL = 60*10


class SettingSchedulingProcess:
    set_to_go: ExecuteSet
    retry: int = RETRY

    def _do_execute_setting(self):
        logging.info(f'executing {self.set_to_go.container.name} {self.set_to_go.temperature}')
        api_execute_setting(self.set_to_go.id)

    def schedule_setting_enter(self):
        logging.info('setting schedule entry')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(
            self.set_to_go.timestamp, 0, self._do_execute_setting)
        scheduler.run()

    def error_setting(self):
        self.set_to_go.status = 'error'
        update_status_in_db(self.set_to_go)
        logging.info(f'failed {self.set_to_go.container.name} {self.set_to_go.temperature}')

    def check_for_errors(self, error_check_retry: int):
        logging.info('checking for api execution failure')
        if error_check_retry == RETRY - 2:
            executed_control_ids = select_from_db(
                ExecuteSetControl.__tablename__,
                select_columns=['control_id'],
                where_condition={'set_id': self.set_to_go.id}, keys=False)
            logging.info(f'executed controls: {len(executed_control_ids)}')
            if not executed_control_ids:
                self.error_setting()

    def get_updated_set_status(self) -> str:
        return select_from_db(
            ExecuteSet.__tablename__, ['status'], {'id': self.set_to_go.id}, keys=False).pop()

    def consider_setting_status(self):
        try:
            self.set_to_go.status = self.get_updated_set_status()
        except IndexError:
            logging.info(f'setting task unavailable')
            exit()
        else:
            if not self.set_to_go.status == 'running':
                logging.info(f'setting task status {self.set_to_go.status}')
                exit()

    def schedule_and_retry_setting(self, setting_retry: int):
        self.consider_setting_status()
        self.schedule_setting_enter()
        logging.info(f'scheduling setting {self.set_to_go.container.name} to {self.set_to_go.temperature}°C')
        if setting_retry:
            setting_retry -= 1
            self.set_to_go.timestamp = int(time()) + SETTING_INTERVAL
            logging.info(f'scheduling api launch {setting_retry - RETRY} ')
            self.check_for_errors(setting_retry)
            self.schedule_and_retry_setting(setting_retry)
        else:
            self.error_setting()

    def execute(self, set_to_go: ExecuteSet):
        self.set_to_go = set_to_go
        if self.retry == RETRY:
            sleep(1)

        if self.set_to_go:
            logging.info(f'setting status {self.set_to_go.status}')
            if self.set_to_go.status == 'running':
                self.schedule_and_retry_setting(self.retry)


def thread_set(executed_set: ExecuteSet):
    thread = Thread(target=SettingSchedulingProcess().execute, args=[executed_set])
    thread.start()
