from pathlib import Path
import subprocess

app_root = Path(__file__).parent.parent.parent / 'taemp_ctrl'
activate_venv = app_root / 'venv' / 'bin' / 'activate'
app_script = app_root / 'src' / 'execute.py'


def execute_task(task_id: int):
    command = f'source {activate_venv}; python {app_script} {str(task_id)}'
    subprocess.call(command, shell=True, executable='/bin/bash')


def initialize_database():
    command = f'source {activate_venv}; python {app_script} --initialize'
    subprocess.call(command, shell=True, executable='/bin/bash')
