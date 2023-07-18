from pathlib import Path
import subprocess


def execute_task(task_id: int):
    app_root = Path(__file__).parent.parent.parent / 'taemp_ctrl'
    activate_venv = app_root / 'venv' / 'bin' / 'activate'
    app_script = app_root / 'src' / 'execute.py'
    command = f'source {activate_venv}; python {app_script} {str(task_id)}'
    subprocess.call(command, shell=True, executable='/bin/bash')
