from .models import Set
from . import db
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

parent_dir = Path(__file__).parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)

key_1 = dotenv_values.get("API_KEY_1")
key_2 = dotenv_values.get("API_KEY_2")
aws_key_id = dotenv_values.get("AWS_KEY_ID")
aws_secret_key = dotenv_values.get("AWS_SECRET_KEY")


@dataclass
class ExecuteSet:
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
    # set_to_go_check = db.session.query(Set).filter_by(id=set_to_go.id).first()
    # print(set_to_go_check)
    # set_to_go.status = set_to_go_check.status

    if set_to_go.status == 'running':
        logging.info(f'scheduling {set_to_go.container} {set_to_go.temperature}')
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(set_to_go.timestamp, 0, execute_set_temperature, kwargs={'run_set': set_to_go})
        scheduler.run()
        logging.info(f'ran {set_to_go.container} {set_to_go.temperature}')
        set_to_go.timestamp += 60
        if retry:
            logging.info('checking and possible retry of setting')
            retry -= 1
            schedule_temperature_setting(set_to_go, retry)
        else:
            logging.info(f'failed {set_to_go.container} {set_to_go.temperature}')
            set_to_go.status = 'error'
            db.session.commit()


def execute_set(executed_set: ExecuteSet):
    thread = Thread(target=schedule_temperature_setting, args=[executed_set])
    thread.start()
