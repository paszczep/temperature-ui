from application.utility.database import (select_from_db, update_status_in_db, ExecuteTask, task_from_dict,)
from application.utility.launch import do_execute_task
from threading import Thread
import sched
from time import time, sleep
from typing import Union
import logging


def check_for_errors():
    if retry == 2:
        executed_control_ids = select_from_db(
            ExecuteSetControl.__tablename__,
            select_columns=['control_id'],
            where_condition={'set_id': set_to_go.id}, keys=False)
        if not executed_control_ids:
            error_setting()


def schedule_temperature_task(schedule_task_id: str):
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
        task_at_hand.status = 'ended'
        update_status_in_db(ended_task)

    task_at_hand = get_task_at_hand()
    if task_at_hand:
        logging.info(f'task status {task_at_hand.status}')
        if task_at_hand.status == 'running':
            schedule_task(task_at_hand)
            if time() < task_at_hand.start + task_at_hand.duration:
                sleep(5*60)
                schedule_temperature_task(schedule_task_id)
            else:
                end_task(task_at_hand)


def thread_task(threaded_task_id: str):
    logging.info(f'threading tasking')
    thread = Thread(target=schedule_temperature_task, args=[threaded_task_id])
    thread.start()
