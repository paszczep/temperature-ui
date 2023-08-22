from flask import Blueprint, render_template, redirect, url_for
from datetime import datetime
from .models import Container, Thermometer, Task, Set, Check
from .form import TaskForm, SetForm
from .process import execute_task, initialize_database
from . import db
from typing import Union
from uuid import uuid4
from random import randint

user_input = Blueprint('input', __name__)


@user_input.route('/task')
def tasks():
    checks = {Check.query.all()}
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=len(containers),
        sets=Set.query.all(),
        checks=checks
    )


def timestamp_from_selection(form: Union[TaskForm, SetForm]) -> int:
    form_date_time = f'{form.date.data} {form.time.data}'
    return int(datetime.timestamp(datetime.strptime(form_date_time, '%Y-%m-%d %H:%M:%S')))


def create_task(form: TaskForm) -> Task:
    return Task(
        id=str(uuid4()),
        start=timestamp_from_selection(form),
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


def create_task_settings(
        form: TaskForm,
        task_container: Container,
) -> Task:
    created_task = create_task(form)
    db.session.add(created_task)
    task_container.task.clear()
    task_container.task = [created_task]
    task_container.thermometers.clear()
    task_container.thermometers.extend(form.choices.data)
    task_container.label = form.name.data
    return created_task


def form_data(task_container: Container, old_task: Union[Task, None]) -> dict:
    return {
        "name": task_container.label,
        "choices": task_container.thermometers,
        "date": (start := datetime.fromtimestamp(old_task.start)).date() if old_task else (now := datetime.now()).date(),
        "time": start.time() if old_task else now.time(),
        "hours": (hours := old_task.duration//3600 if old_task else 30),
        "minutes": (old_task.duration % hours)/60 if old_task else 0,
        "t_start": old_task.t_start if old_task else 40,
        "t_max": old_task.t_max if old_task else 40,
        "t_min": old_task.t_min if old_task else 30,
        "t_freeze": old_task.t_freeze if old_task else -20
    }


def render_task_form(form: TaskForm, task_container: Container, all_containers: list[Container]):
    return render_template(
        "task.html",
        form=form,
        task_container=task_container,
        all_containers=all_containers)


def delete_old_task(del_task: Task):
    if del_task:
        db.session.delete(del_task)


@user_input.route("/task/<container>", methods=["POST", "GET"])
def task(container):

    task_container = Container.query.get(container)
    all_containers = Container.query.all()
    existing_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, existing_task))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        if form.cancel.data:
            pass
        if form.save.data:
            delete_old_task(existing_task)
            create_task_settings(form, task_container)
            db.session.commit()
        if form.submit.data:
            delete_old_task(existing_task)
            new_task = create_task_settings(form, task_container)
            new_task.status = 'running'
            db.session.commit()
            execute_task(task_id=new_task.id)

    return render_task_form(form, task_container, all_containers)