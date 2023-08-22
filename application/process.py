from .models import Set
from pathlib import Path
import subprocess
from threading import Thread
import sched
from time import time, sleep


app_root = Path(__file__).parent.parent.parent / 'taemp_ctrl'
activate_venv = app_root / 'venv' / 'bin' / 'activate'
app_script = app_root / 'src' / 'execute.py'


def execute_task(task_id: str):
    command = f'source {activate_venv}; python {app_script} {task_id}'
    subprocess.call(command, shell=True, executable='/bin/bash')


def initialize_database():
    command = f'source {activate_venv}; python {app_script} --initialize'
    subprocess.call(command, shell=True, executable='/bin/bash')


def check_containers():
    command = f'source {activate_venv}; python {app_script} --check'
    subprocess.call(command, shell=True, executable='/bin/bash')


def set_temperature(set_id: str):
    command = f'source {activate_venv}; python {app_script} --set={set_id}'
    subprocess.call(command, shell=True, executable='/bin/bash')


def schedule_temperature_setting(set_to_go: Set):
    scheduler = sched.scheduler(time, sleep)
    scheduler.enterabs(set_to_go.timestamp, 0, set_temperature, kwargs={'set_id': set_to_go.id})
    scheduler.run()


def execute_set(executed_set: Set):
    thread = Thread()
