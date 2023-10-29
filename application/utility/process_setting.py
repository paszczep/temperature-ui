from application.utility.database_query import select_from_db, update_status_in_db
from application.utility.models_process import ExecuteSet, ExecuteSetControl
from application.utility.launch import execute_setting
from threading import Thread
import sched
from time import time, sleep
from typing import Union
import logging

RETRY = 10
SETTING_INTERVAL = 60*10


def setting_schedule_process(set_to_go: ExecuteSet, retry: int = RETRY):
    def do_execute_setting(run_set: ExecuteSet):
        logging.info(f'executing {run_set.container.name} {run_set.temperature}')
        execute_setting(run_set.id)

    def schedule_setting_enter():
        logging.info('setting schedule entry')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(set_to_go.timestamp, 0, do_execute_setting, kwargs={'run_set': set_to_go})
        scheduler.run()

    def error_setting():
        set_to_go.status = 'error'
        update_status_in_db(set_to_go)
        logging.info(f'failed {set_to_go.container.name} {set_to_go.temperature}')

    def check_for_errors(error_check_retry: int):
        logging.info('checking for api execution failure')
        if error_check_retry == RETRY - 2:
            executed_control_ids = select_from_db(
                ExecuteSetControl.__tablename__,
                select_columns=['control_id'],
                where_condition={'set_id': set_to_go.id}, keys=False)
            if not executed_control_ids:
                error_setting()

    def schedule_and_retry_setting(setting_retry: int):
        schedule_setting_enter()
        logging.info(f'scheduling setting {set_to_go.container.name} to {set_to_go.temperature}°C')
        time_now = int(time())
        set_to_go.timestamp = time_now + SETTING_INTERVAL
        if setting_retry:
            logging.info(f'scheduling api launch {setting_retry - RETRY} ')
            setting_retry -= 1
            check_for_errors(setting_retry)
            setting_schedule_process(set_to_go, setting_retry)
        else:
            error_setting()

    def get_updated_set_status() -> str:
        return select_from_db(
            ExecuteSet.__tablename__, ['status'], {'id': set_to_go.id}, keys=False).pop()

    if retry == RETRY:
        sleep(30)
    try:
        set_to_go.status = get_updated_set_status()
    except IndexError:
        logging.info(f'setting task already deleted')
        exit()
    if set_to_go:
        logging.info(f'setting status {set_to_go.status}')
        if set_to_go.status == 'running':
            schedule_and_retry_setting(retry)


def thread_set(executed_set: ExecuteSet):
    thread = Thread(target=setting_schedule_process, args=[executed_set])
    thread.start()
