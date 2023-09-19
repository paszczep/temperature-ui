from .database import select_from_db, update_status_in_db, ExecuteTask, ExecuteSet, task_from_dict
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
run_local_api = False


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


def schedule_temperature_setting(set_to_go: ExecuteSet, retry: int = 5):
    def execute_set_temperature(run_set: ExecuteSet):
        logging.info(f'executing {run_set.container} {run_set.temperature}')
        if run_local_api:
            execute_local(setting=run_set.id)
        else:
            run_lambda(setting=run_set.id)

    def schedule_setting():
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(set_to_go.timestamp, 0, execute_set_temperature, kwargs={'run_set': set_to_go})
        scheduler.run()

    def schedule_and_retry_setting(setting_retry: int):
        schedule_setting()
        logging.info(f'ran {set_to_go.container} {set_to_go.temperature}')
        set_to_go.timestamp = int(time()) + 3*60
        if setting_retry:
            logging.info('checking and possible retry of setting')
            setting_retry -= 1
            schedule_temperature_setting(set_to_go, setting_retry)
        else:
            set_to_go.status = 'error'
            update_status_in_db(set_to_go)
            logging.info(f'failed {set_to_go.container} {set_to_go.temperature}')

    def update_set_status():
        set_to_go.status = select_from_db(ExecuteSet.__tablename__, ['status'], {'id': set_to_go.id}, keys=False).pop()

    def end_set(ended_set: ExecuteSet):
        ended_set.status = 'ended'
        update_status_in_db(ended_set)

    # sleep(30)
    update_set_status()
    if set_to_go.status == 'running':
        schedule_and_retry_setting(retry)
    elif set_to_go.status == 'cancelled':
        end_set(set_to_go)


def thread_set(executed_set: ExecuteSet):
    thread = Thread(target=schedule_temperature_setting, args=[executed_set])
    thread.start()


def schedule_temperature_task(schedule_task_id: str):
    def get_task_at_hand() -> Union[ExecuteTask, None]:
        select_tasks = select_from_db(
                table_name=ExecuteTask.__tablename__,
                where_condition={'id': schedule_task_id},
                keys=True)
        return [task_from_dict(t) for t in select_tasks].pop() if select_tasks else None

    def do_execute_task(exec_task_id: str):
        if run_local_api:
            execute_local(task=exec_task_id)
        else:
            run_lambda(task=exec_task_id)

    def schedule_task(scheduled_task: ExecuteTask):
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(scheduled_task.start, 0, do_execute_task, kwargs={'exec_task_id': scheduled_task.id})
        scheduler.run()

    def end_task(ended_task: ExecuteTask):
        task_at_hand.status = 'ended'
        update_status_in_db(ended_task)

    task_at_hand = get_task_at_hand()
    if task_at_hand:
        if task_at_hand.status == 'running':
            schedule_task(task_at_hand)
            if time() < task_at_hand.start + task_at_hand.duration:
                sleep(15*60)
                schedule_temperature_task(schedule_task_id)
            else:
                end_task(task_at_hand)
        elif task_at_hand.status == 'cancelled':
            end_task(task_at_hand)


def thread_task(threaded_task_id: str):
    thread = Thread(target=schedule_temperature_task, args=[threaded_task_id])
    thread.start()
