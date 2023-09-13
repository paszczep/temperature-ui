from .models import Set
from . import db
from pathlib import Path
import subprocess
from threading import Thread
import sched
from time import time, sleep
from os import getenv
from hashlib import sha256
import boto3
import json

app_root = Path(__file__).parent.parent.parent / 'taemp_ctrl'
activate_venv = app_root / 'venv' / 'bin' / 'activate'
app_script = app_root / 'src' / 'execute.py'
key_1 = getenv("API_KEY_1")
key_2 = getenv("API_KEY_2")
aws_key_id = getenv("AWS_KEY_ID")
aws_secret_key = getenv("AWS_SECRET_KEY")


def key_hash(key: str) -> str:
    return sha256(key.encode("utf-8")).hexdigest()


def run_lambda():
    client = boto3.client('lambda', 'eu-central-1', aws_access_key_id=aws_key_id, aws_secret_access_key=aws_secret_key)
    response = client.invoke(
        FunctionName="temp_ctrl_lambda",
        Payload=json.dumps({
            "key_1": key_1,
            "key_2": key_hash(key_2),
            "initialize": False,
            "check": True,
            "task": None,
            "set": None
        })
    )
    return response['Payload'].read().decode("utf-8")


_dict = {'ResponseMetadata': '',
         'StatusCode': 200,
         'FunctionError': 'Unhandled',
         'ExecutedVersion': '$LATEST',
         'Payload': '< botocore.response.StreamingBody object at 0x7f203727a320 >'}

def command_beginning() -> str:
    return f'source {activate_venv}; ' \
           f'python {app_script} ' \
           f'--key_1="{key_1}" ' \
           f'--key_2="{key_hash(key_2)}"'


def execute_task(task_id: str):
    command = f'{command_beginning()} --task={task_id}'
    subprocess.call(command, shell=True, executable='/bin/bash')


def initialize_database():
    command = f'{command_beginning()} --initialize'
    subprocess.call(command, shell=True, executable='/bin/bash')


def check_containers():
    command = f'{command_beginning()} --check'
    subprocess.call(command, shell=True, executable='/bin/bash')


def execute_set_temperature(run_set: Set):
    command = f'{command_beginning()} --set={run_set.id}'
    subprocess.call(command, shell=True, executable='/bin/bash')


def schedule_temperature_setting(set_to_go: Set, retry: int = 5):
    sleep(30)
    set_to_go.status = Set.query.filter_by(id=set_to_go.id).first().status
    if set_to_go.status == 'running':
        scheduler = sched.scheduler(time, sleep)
        scheduler.enterabs(set_to_go.timestamp, 0, execute_set_temperature, kwargs={'run_set': set_to_go})
        scheduler.run()
        set_to_go.timestamp += 3 * 60
        if retry:
            retry -= 1
            schedule_temperature_setting(set_to_go, retry)
        else:
            set_to_go.status = 'error'
            db.session.commit()


def execute_set(executed_set: Set):
    thread = Thread(target=schedule_temperature_setting, args=[executed_set])
    thread.start()
