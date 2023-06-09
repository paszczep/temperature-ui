from flask import Blueprint, render_template
from datetime import datetime
from .models import Container, Thermometer, Task
from .form import TaskForm
from . import db
from typing import Union

input = Blueprint('input', __name__)


@input.route('/task')
def tasks():
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=len(containers)
    )


def form_data(task_container: Container, old_task: Union[Task, None]) -> dict:
    now = datetime.now()
    return {
        "name": task_container.label,
        "choices": task_container.thermometers,
        "date": now.date(),
        "time": now.time(),
        "hours": (hours := old_task.duration//3600 if old_task is not None else 30),
        "minutes": (old_task.duration % hours)/60 if old_task is not None else 0,
        "t_start": old_task.t_start if old_task is not None else 40,
        "t_max": old_task.t_max if old_task is not None else 40,
        "t_min": old_task.t_min if old_task is not None else 30,
        "t_freeze": old_task.t_freeze if old_task is not None else -20
    }


def start_from_form(form: TaskForm) -> int:
    return int(datetime.timestamp(datetime.strptime(f'{form.date.data} {form.time.data}', '%Y-%m-%d %H:%M:%S')))


def create_task(form: TaskForm) -> Task:
    return Task(
        id=len(Task.query.all()) + 1,
        start=start_from_form(form),
        duration=form.hours.data * 3600 + form.minutes.data * 60,
        t_start=form.t_start.data,
        t_min=form.t_min.data,
        t_max=form.t_max.data,
        t_freeze=form.t_freeze.data,
        status='new',
    )


def retrieve_task(task_container: Container) -> Union[Task, None]:
    old_task = task_container.task
    return old_task[0] if old_task else None


@input.route("/task/<container>", methods=["POST", "GET"])
def task(container):
    task_container = Container.query.get(container)
    all_containers = Container.query.all()
    old_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, old_task))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        new_task = create_task(form)
        if old_task:
            db.session.delete(old_task)
            new_task.id = old_task.id
        db.session.add(new_task)
        task_container.task.clear()
        task_container.task = [new_task]
        task_container.thermometers.clear()
        task_container.thermometers.extend(form.choices.data)
        task_container.label = form.name.data
        db.session.commit()

    return render_template(
        "task.html",
        form=form,
        task_container=task_container,
        all_containers=all_containers)
