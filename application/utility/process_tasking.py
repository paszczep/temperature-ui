from application.utility.database_query import select_from_db, update_status_in_db
from application.utility.models_process import (ExecuteTask, task_from_dict, ExecuteTaskControl, ExecuteCheck,
                                                ExecuteTaskRead)
from application.utility.launch import do_execute_task
from threading import Thread
import sched
from time import time, sleep
from typing import Union
import logging

SETTING_INTERVAL = 60 * 30


def error_task(bad_task: ExecuteTask):
    logging.info('task error')
    bad_task.status = 'error'
    update_status_in_db(bad_task)


def check_for_api_failure(task_at_hand: ExecuteTask, setting_count: int):
    logging.info('checking for api execution failure')
    if setting_count == 2:
        _control_ids = select_from_db(
            ExecuteTaskControl.__tablename__,
            select_columns=['control_id'],
            where_condition={'task_id': task_at_hand.id}, keys=False)
        logging.info(f'executed controls {len(_control_ids)}')
        _checks = [ExecuteCheck(**c) for c in select_from_db(
            ExecuteCheck.__tablename__,
            select_columns=['id'],
            where_condition={'container': task_at_hand.container}, keys=True)]
        _checks = [c for c in _checks if c.timestamp > task_at_hand.start]
        _read_ids = select_from_db(
            ExecuteTaskRead.__tablename__,
            select_columns=['read_id'],
            where_condition={'task_id': task_at_hand.id}, keys=False)
        if not _read_ids or (not _control_ids and not _checks):
            logging.warning('api execution failure')
            error_task(task_at_hand)


def tasking_scheduling(schedule_task_id: str, setting_count: int = 0):
    def get_task_at_hand() -> Union[ExecuteTask, None]:
        logging.info('retrieving task at hand')
        select_tasks = select_from_db(
                table_name=ExecuteTask.__tablename__,
                where_condition={'id': schedule_task_id}, keys=True)
        return [task_from_dict(tsk) for tsk in select_tasks].pop() if select_tasks else None

    def schedule_task(scheduled_task: ExecuteTask):
        logging.info(f'scheduling task {scheduled_task.container}')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(scheduled_task.start, 0, do_execute_task, kwargs={'exec_task_id': scheduled_task.id})
        scheduler.run()

    def end_task(ended_task: ExecuteTask):
        logging.info('ending task')
        task_at_hand.status = 'ended'
        update_status_in_db(ended_task)

    task_at_hand = get_task_at_hand()
    if task_at_hand:
        logging.info(f'task status {task_at_hand.status}')
        if task_at_hand.status == 'running':
            schedule_task(task_at_hand)
            if time() < task_at_hand.start + task_at_hand.duration + SETTING_INTERVAL*5:
                sleep(SETTING_INTERVAL)
                setting_count += 1
                logging.info(f'setting count {setting_count}')
                check_for_api_failure(task_at_hand, setting_count)
                tasking_scheduling(schedule_task_id, setting_count)
            else:
                error_task(task_at_hand)


def thread_task(threaded_task_id: str):
    logging.info(f'threading tasking api launch')
    thread = Thread(target=tasking_scheduling, args=[threaded_task_id])
    thread.start()
