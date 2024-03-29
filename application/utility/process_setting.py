from application.utility.database_query import select_from_db, update_status_in_db
from application.utility.models_process import ExecuteSet, ExecuteSetControl
from application.utility.launch import api_execute_setting
from application.utility.mail import Email
from threading import Thread
import sched
from time import time, sleep
import logging

MAX_RETRY = 4
SETTING_INTERVAL = 60*10


class SettingSchedulingProcess:
    set_to_go: ExecuteSet
    retry_count: int = 0
    sent_report: bool = False

    def email_report(self):
        _status = self.set_to_go.status
        if not self.sent_report and _status in ('ended', 'error'):
            _message = f'{self.set_to_go.container} {self.set_to_go.temperature} {_status}'
            Email().send(message=_message, email=self.set_to_go.email)
            self.sent_report = True

    def consider_setting_status(self):
        try:
            self.set_to_go.status = self.get_updated_set_status()
            logging.info(f'setting status: {self.set_to_go.status}')
        except IndexError:
            logging.info(f'setting task unavailable')
            exit()
        else:
            if not self.set_to_go.status == 'running':
                logging.info(f'exit process')
                self.email_report()
                exit()

    def _do_execute_setting(self):
        self.consider_setting_status()
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

    def check_for_errors(self):
        logging.info('checking for api execution failure')
        if self.retry_count == 2:
            executed_control_ids = select_from_db(
                ExecuteSetControl.__tablename__,
                columns=['control_id'],
                where_condition={'set_id': self.set_to_go.id}, keys=False)
            logging.info(f'executed controls: {len(executed_control_ids)}')
            if not executed_control_ids:
                self.error_setting()

    def get_updated_set_status(self) -> str:
        return select_from_db(
            ExecuteSet.__tablename__, ['status'], {'id': self.set_to_go.id}, keys=False).pop()

    def schedule_and_retry_setting(self):
        self.consider_setting_status()
        self.schedule_setting_enter()
        logging.info(f'scheduling setting {self.set_to_go.container.name} to {self.set_to_go.temperature}°C')
        if self.retry_count <= MAX_RETRY:
            self.retry_count += 1
            self.set_to_go.timestamp = int(time()) + SETTING_INTERVAL
            logging.info(f'scheduling api launch {self.retry_count} ')
            self.check_for_errors()
            self.schedule_and_retry_setting()
        elif self.set_to_go.status == 'running':
            self.error_setting()

    def execute(self, set_to_go: ExecuteSet):
        self.set_to_go = set_to_go
        sleep(15)
        self.schedule_and_retry_setting()


def thread_set(executed_set: ExecuteSet):
    thread = Thread(target=SettingSchedulingProcess().execute, args=[executed_set])
    thread.start()
