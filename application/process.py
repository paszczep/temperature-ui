from .database import select_from_db
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
from dataclasses import dataclass
from psycopg2 import connect

parent_dir = Path(__file__).parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)

key_1 = dotenv_values.get("API_KEY_1")
key_2 = dotenv_values.get("API_KEY_2")
aws_key_id = dotenv_values.get("AWS_KEY_ID")
aws_secret_key = dotenv_values.get("AWS_SECRET_KEY")
run_local = dotenv_values.get("AWS_SECRET_KEY")
print('run local', run_local)


def db_connection_and_cursor():

    db_config = {
        "host": dotenv_values.get('DB_HOST'),
        "dbname": dotenv_values.get('DB_NAME'),
        "user": dotenv_values.get('DB_USER'),
        "password": dotenv_values.get('DB_PASSWORD'),
        "port": dotenv_values.get('DB_PORT')
    }

    db_connection = connect(**db_config)
    db_cursor = db_connection.cursor()
    return db_connection, db_cursor


@dataclass
class ExecuteSet:
    __tablename__ = 'temp_set'
    id: str
    status: str
    temperature: int
    timestamp: int
    container: str


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


def execute_task(task_id: str):
    run_lambda(task=task_id)


def initialize_database():
    run_lambda(initialize=True)


def check_containers():
    run_lambda(check=True)


def execute_set_local(set_id: str):
    payload = json.dumps({
        "key_1": key_1,
        "key_2": key_hash(key_2),
        "initialize": False,
        "check": True,
        "task": None,
        "set": set_id
    })

    command = f"""
    curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{payload}'"""
    subprocess.call(command, shell=True, executable='/bin/bash')


def execute_set_temperature(run_set: ExecuteSet):
    logging.info(f'executing {run_set.container} {run_set.temperature}')
    # run_lambda(setting=run_set.id)
    execute_set_local(set_id=run_set.id)


def schedule_temperature_setting(set_to_go: ExecuteSet, retry: int = 5):
    # sleep(30)
    set_status = select_from_db(ExecuteSet.__tablename__, ['status'], {'id': set_to_go.id}, keys=False).pop()
    if set_status == 'running':
        logging.info(f'scheduling {set_to_go.container} {set_to_go.temperature}')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(set_to_go.timestamp, 0, execute_set_temperature, kwargs={'run_set': set_to_go})
        scheduler.run()
        logging.info(f'ran {set_to_go.container} {set_to_go.temperature}')
        set_to_go.timestamp = int(time()) + 60
        if retry:
            logging.info('checking and possible retry of setting')
            retry -= 1
            schedule_temperature_setting(set_to_go, retry)
        else:
            logging.info(f'failed {set_to_go.container} {set_to_go.temperature}')


def thread_set(executed_set: ExecuteSet):
    thread = Thread(target=schedule_temperature_setting, args=[executed_set])
    thread.start()


@dataclass
class ExecuteTask:
    __tablename__ = 'task'
    id: str
    start: int
    duration: int
    t_start: int
    t_min: int
    t_max: int
    t_freeze: int
    status: str
    container: str
    reads: list
    controls: list


def task_from_dict(t: dict) -> ExecuteTask:
    return ExecuteTask(
        id=t['id'],
        start=t['start'],
        duration=t['duration'],
        t_start=t['t_start'],
        t_min=t['t_min'],
        t_max=t['t_max'],
        t_freeze=t['t_freeze'],
        status=t['status'],
        container='',
        reads=list(),
        controls=list()
    )


def execute_task_local(task_id: str):
    payload = json.dumps({
        "key_1": key_1,
        "key_2": key_hash(key_2),
        "initialize": False,
        "check": True,
        "task": task_id,
        "set": None
    })

    command = f"""
    curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{payload}'"""
    subprocess.call(command, shell=True, executable='/bin/bash')


def schedule_temperature_check(schedule_task_id: str):
    def get_task_at_hand() -> ExecuteTask:
        return [task_from_dict(t) for t in select_from_db(
                table_name=ExecuteTask.__tablename__,
                where_condition={'id': schedule_task_id},
                keys=True)].pop()

    task_at_hand = get_task_at_hand()
    if task_at_hand.status == 'running':
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(task_at_hand.start, 0, execute_task_local, kwargs={'task_id': task_at_hand})
        scheduler.run()
        if time() < task_at_hand.start + task_at_hand.duration:
            sleep(10)
            schedule_temperature_check(schedule_task_id)


def thread_task(execute_task: ExecuteTask):
    thread = Thread(target=schedule_temperature_check, args=[execute_task])
    thread.start()