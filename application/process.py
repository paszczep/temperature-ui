from .database import select_from_db, update_status_in_db, ExecuteTask, ExecuteSet, task_from_dict, ExecuteSetControl
from threading import Thread
import sched
from time import time, sleep
from hashlib import sha256
import boto3
import json
from typing import Union
from pathlib import Path
from dotenv import dotenv_values
import logging
import subprocess

parent_dir = Path(__file__).parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)

key_1 = dotenv_values.get("API_KEY_1")
key_2 = dotenv_values.get("API_KEY_2")
aws_key_id = dotenv_values.get("AWS_KEY_ID")
aws_secret_key = dotenv_values.get("AWS_SECRET_KEY")
run_local_api = True

if run_local_api:
    logging.info('local api')
else:
    logging.info('remote api')


def key_hash(key: str) -> str:
    return sha256(key.encode("utf-8")).hexdigest()


def run_lambda(
        initialize: bool = False,
        check: bool = False,
        task: Union[str, None] = None,
        setting: Union[str, None] = None
):
    client = boto3.client('lambda', 'eu-central-1', aws_access_key_id=aws_key_id, aws_secret_access_key=aws_secret_key)
    payload = json.dumps({
        "key_1": key_1,
        "key_2": key_hash(key_2),
        "initialize": initialize,
        "check": check,
        "task": task,
        "set": setting
    })
    response = client.invoke(
        FunctionName="temp_ctrl_lambda",
        Payload=payload
    )
    return response['Payload'].read().decode("utf-8")


def execute_local(
        initialize: bool = False,
        check: bool = False,
        task: Union[str, None] = None,
        setting: Union[str, None] = None):
    payload = json.dumps({
        "key_1": key_1,
        "key_2": key_hash(key_2),
        "initialize": initialize,
        "check": check,
        "task": task,
        "set": setting
    })

    command = f"""
    curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{payload}'"""
    subprocess.call(command, shell=True, executable='/bin/bash')


def initialize_database():
    if run_local_api:
        execute_local(initialize=True)
    else:
        run_lambda(initialize=True)


def check_containers():
    if run_local_api:
        execute_local(check=True)
    else:
        run_lambda(check=True)


def schedule_temperature_setting(set_to_go: ExecuteSet, retry: int = 4):
    def execute_set_temperature(run_set: ExecuteSet):
        logging.info(f'executing {run_set.container.name} {run_set.temperature}')
        if run_local_api:
            execute_local(setting=run_set.id)
        else:
            run_lambda(setting=run_set.id)

    def schedule_setting():
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(set_to_go.timestamp, 0, execute_set_temperature, kwargs={'run_set': set_to_go})
        scheduler.run()

    def error_set():
        set_to_go.status = 'error'
        update_status_in_db(set_to_go)
        logging.info(f'failed {set_to_go.container.name} {set_to_go.temperature}')

    def check_for_errors(the_now: int, setting_operation: ExecuteSet):
        if retry == 2:
            executed_control_ids = select_from_db(
                ExecuteSetControl.__tablename__,
                select_columns=['control_id'],
                where_condition={'set_id': set_to_go.id}, keys=False)
            if (the_now > setting_operation.timestamp + 10*60) and not executed_control_ids:
                error_set()

    def schedule_and_retry_setting(setting_retry: int):
        schedule_setting()
        logging.info(f'scheduling setting {set_to_go.container.name} to {set_to_go.temperature}°C')
        time_now = int(time())
        set_to_go.timestamp = time_now + 5*60
        if setting_retry:
            logging.info('checking and possible setting')
            setting_retry -= 1
            schedule_temperature_setting(set_to_go, setting_retry)
        else:
            error_set()

    def get_updated_set_status() -> str:
        return select_from_db(
            ExecuteSet.__tablename__, ['status'], {'id': set_to_go.id}, keys=False).pop()

    sleep(30)
    try:
        set_to_go.status = get_updated_set_status()
    except IndexError:
        exit()
    logging.info(f'setting status {set_to_go.status}')
    if set_to_go.status == 'running':
        schedule_and_retry_setting(retry)


def thread_set(executed_set: ExecuteSet):
    thread = Thread(target=schedule_temperature_setting, args=[executed_set])
    thread.start()


def schedule_temperature_task(schedule_task_id: str):
    def get_task_at_hand() -> Union[ExecuteTask, None]:
        logging.info('retrieving task at hand')
        select_tasks = select_from_db(
                table_name=ExecuteTask.__tablename__,
                where_condition={'id': schedule_task_id}, keys=True)
        return [task_from_dict(tsk) for tsk in select_tasks].pop() if select_tasks else None

    def do_execute_task(exec_task_id: str):
        logging.info('executing task')
        if run_local_api:
            execute_local(task=exec_task_id)
        else:
            run_lambda(task=exec_task_id)

    def schedule_task(scheduled_task: ExecuteTask):
        logging.info(f'scheduling task {scheduled_task.container}')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(scheduled_task.start, 0, do_execute_task, kwargs={'exec_task_id': scheduled_task.id})
        scheduler.run()

    def end_task(ended_task: ExecuteTask):
        task_at_hand.status = 'ended'
        update_status_in_db(ended_task)

    task_at_hand = get_task_at_hand()
    logging.info(f'task status {task_at_hand.status}')
    if task_at_hand:
        if task_at_hand.status == 'running':
            schedule_task(task_at_hand)
            if time() < task_at_hand.start + task_at_hand.duration:
                sleep(5*60)
                schedule_temperature_task(schedule_task_id)
            else:
                end_task(task_at_hand)


def thread_task(threaded_task_id: str):
    thread = Thread(target=schedule_temperature_task, args=[threaded_task_id])
    thread.start()
