from flask import Blueprint, render_template, redirect
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


def timestamp_from_selection(form: Union[TaskForm, SetForm]) -> int:
    form_date_time = f'{form.date.data} {form.time.data}'
    print(form_date_time)
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
    print(old_task)
    return old_task[0] if old_task else None


def render_task_form(form: TaskForm, task_container: Container, all_containers: list[Container]):
    return render_template(
        "task.html",
        form=form,
        task_container=task_container,
        all_containers=all_containers)


def save_task_to_db_return_id(
        form: TaskForm,
        task_container: Container,
        old_task: Union[Task, None]
) -> Task:

    def del_old_task():
        if old_task:
            db.session.delete(old_task)

    def save_task_to_db():
        new_task = create_task(form)
        del_old_task()
        db.session.add(new_task)
        db.session.commit()
        return new_task

    def save_container_to_db(created_task: Task):
        task_container.task.clear()
        task_container.task = [created_task]
        task_container.thermometers.clear()
        task_container.thermometers.extend(form.choices.data)
        task_container.label = form.name.data

    new_task = save_task_to_db()
    save_container_to_db(new_task)
    db.session.commit()
    return new_task


@user_input.route("/task/<container>", methods=["POST", "GET"])
def task(container):

    task_container = Container.query.get(container)
    all_containers = Container.query.all()
    old_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, old_task))
    form.choices.query = Thermometer.query.all()

    if form.cancel.data:
        pass

    if form.save.data:
        save_task_to_db_return_id(form, task_container, old_task)

    if form.validate_on_submit():
        new_task = save_task_to_db_return_id(form, task_container, old_task)
        execute_task(task_id=new_task_id)

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
            'date': now.date(),
            'time': now.time(),
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


@user_input.route("/set/<container>", methods=["POST", "GET"])
def temp_set(container):
    set_container = Container.query.get(container)
    all_containers = Container.query.all()

    old_set = retrieve_old_set(set_container)

    set_form = SetForm(data=set_data(set_container, old_set))

    if set_form.cancel.data:
        pass

    if set_form.save.data:
        new_set = create_set(set_form, set_container)
        save_set_to_db(new_set, old_set)

    if set_form.validate_on_submit():
        new_set = create_set(set_form, set_container)
        new_set.status = 'running'
        save_set_to_db(new_set, old_set)

    return render_set_form(set_form, set_container, all_containers)


