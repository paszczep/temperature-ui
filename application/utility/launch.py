from hashlib import sha256
import boto3
import json
from typing import Union
from pathlib import Path
from dotenv import dotenv_values
import logging
import subprocess

parent_dir = Path(__file__).parent.parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)

key_1 = dotenv_values.get("API_KEY_1")
key_2 = dotenv_values.get("API_KEY_2")
aws_key_id = dotenv_values.get("AWS_KEY_ID")
aws_secret_key = dotenv_values.get("AWS_SECRET_KEY")
run_local_api = False

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


def api_local_or_lambda(**kwargs):
    if run_local_api:
        logging.info('launching local api')
        execute_local(**kwargs)
    else:
        logging.info('launching remote api')
        run_lambda(**kwargs)


def initialize_database():
    logging.info(f'launching api to initialize database')
    api_local_or_lambda(initialize=True)


def check_containers():
    logging.info(f'launching api for checking containers')
    api_local_or_lambda(check=True)


def do_execute_task(exec_task_id: str):
    logging.info(f'launching api for task execution')
    api_local_or_lambda(task=exec_task_id)


def execute_setting(run_set_id: str):
    logging.info(f'launching api for setting execution')
    api_local_or_lambda(setting=run_set_id)
