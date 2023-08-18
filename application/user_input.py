from flask import Blueprint, render_template, redirect, url_for
from datetime import datetime
from .models import Container, Thermometer, Task, Set
from .form import TaskForm, SetForm
from .process import execute_task, initialize_database
from . import db
from typing import Union
from uuid import uuid4
from random import randint

user_input = Blueprint('input', __name__)


@user_input.route("/initialize", methods=["POST"])
def init_db():
    initialize_database()
    return redirect('/task')


@user_input.route('/task')
def tasks():
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=len(containers))


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
    now = datetime.now()
    if old_task:
        start_datetime = datetime.fromtimestamp(old_task.start)
    return {
        "name": task_container.label,
        "choices": task_container.thermometers,
        "date": start_datetime.date() if old_task else now.date(),
        "time": start_datetime.time() if old_task else now.time(),
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
    old_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, old_task))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        if form.cancel.data:
            pass
        if form.save.data:
            delete_old_task(old_task)
            create_task_settings(form, task_container)
            db.session.commit()
        if form.submit.data:
            delete_old_task(old_task)
            new_task = create_task_settings(form, task_container)
            new_task.status = 'running'
            db.session.commit()
            execute_task(task_id=new_task.id)

    return render_task_form(form, task_container, all_containers)


def render_set_form(form: SetForm, container: Container, all_containers: list[Container]):
    return render_template(
        "set.html",
        form=form,
        task_container=container,
        all_containers=all_containers)


def set_data(set_container: Container, old_set: Union[Set, None]) -> dict:
    now = datetime.now()
    return {'name': set_container.label,
            'date': (set_datetime := datetime.fromtimestamp(old_set.timestamp)).date() if old_set else now.date(),
            'time': set_datetime.time() if old_set else now.time(),
            'temperature': old_set.temperature if old_set else 0
            }


def retrieve_old_set(set_container: Container) -> Union[Set, None]:
    old_set = Set.query.filter_by(container=set_container.name).first()
    if old_set:
        if old_set.status != 'canceled':
            return old_set
    return None


def create_set(set_form: SetForm, set_container: Container) -> Set:
    return Set(
        id=str(uuid4()),
        status='new',
        temperature=set_form.temperature.data,
        timestamp=timestamp_from_selection(set_form),
        container=set_container.name
    )


def save_container_label_to_db(container: Container, form: Union[SetForm, TaskForm]):
    container.label = form.name.data
    db.session.commit()


def save_set_to_db(new_set: Set, old_set: Union[Set, None]):
    if old_set:
        db.session.delete(old_set)
    db.session.add(new_set)
    db.session.commit()


@user_input.route("/set/<container>", methods=["POST", "GET"])
def temp_set(container):
    set_container = Container.query.get(container)
    all_containers = Container.query.all()
    old_set = retrieve_old_set(set_container)
    set_form = SetForm(data=set_data(set_container, old_set))

    if set_form.validate_on_submit():
        if set_form.cancel.data:
            pass
        else:
            set_container.label = set_form.name.data
        if set_form.save.data:
            new_set = create_set(set_form, set_container)
            save_set_to_db(new_set, old_set)
        if set_form.submit.data:
            new_set = create_set(set_form, set_container)
            new_set.status = 'running'
            save_set_to_db(new_set, old_set)

    return render_set_form(set_form, set_container, all_containers)


