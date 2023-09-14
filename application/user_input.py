from flask import Blueprint, render_template
from flask_login import login_required
from .models import Container, Thermometer, Task, Set, Control
from .form import TaskForm, SetForm
from .process import execute_task, execute_set, ExecuteSet
from . import db
from typing import Union
from uuid import uuid4
from humanize import naturaltime
from time import time
from datetime import datetime
from datetime import timedelta


user_input = Blueprint('input', __name__)


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
        all_containers=all_containers,
        status=task_container.task[0].status if task_container.task else None
    )


def delete_old_task(del_task: Task):
    if del_task:
        db.session.delete(del_task)


@user_input.route("/task/<container>", methods=["POST", "GET"])
@login_required
def task(container):

    task_container = Container.query.get(container)
    all_containers = Container.query.all()
    existing_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, existing_task))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        if form.cancel.data:
            delete_old_task(existing_task)
            db.session.commit()
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


def render_set_template(form: SetForm, container: Container, all_containers: list[Container]):
    controls = [{
        'timestamp': naturaltime(timedelta(seconds=(time() - ctrl.timestamp))),
        'temperature': ctrl.target_setpoint
    }
        for ctrl in container.set[0].controls]

    return render_template(
        "set.html",
        form=form,
        task_container=container,
        all_containers=all_containers,
        status=container.set[0].status if container.set else None,
        controls=controls
    )


def set_data(set_container: Container, old_set: Union[Set, None]) -> dict:
    now = datetime.now()
    return {'name': set_container.label,
            'date': (set_datetime := datetime.fromtimestamp(old_set.timestamp)).date() if old_set else now.date(),
            'time': set_datetime.time() if old_set else now.time(),
            'temperature': old_set.temperature if old_set else 0
            }


def retrieve_set(set_container: Container) -> Union[Task, None]:
    old_set = set_container.set
    return old_set[0] if old_set else None


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
        container=[set_container]
    )


def save_container_label_to_db(container: Container, form: Union[SetForm, TaskForm]):
    container.label = form.name.data
    db.session.commit()


@user_input.route("/set/<container>", methods=["POST", "GET"])
@login_required
def temp_set(container):

    def save_set_to_db(created_set: Set, old_set: Union[Set, None]):
        if old_set:
            db.session.delete(old_set)
        db.session.add(created_set)
        db.session.commit()

    def cancel_set(cancelled_set: Union[Set, None]):
        if cancelled_set:
            if cancelled_set.status in ('new', 'ended'):
                db.session.delete(cancelled_set)
            elif cancelled_set.status == 'running':
                cancelled_set.status = 'cancelled'
            db.session.commit()

    set_container = Container.query.get(container)
    all_containers = Container.query.all()
    existing_set = retrieve_set(set_container)
    set_form = SetForm(data=set_data(set_container, existing_set))

    if set_form.validate_on_submit():
        if set_form.cancel.data:
            cancel_set(existing_set)
        else:
            set_container.label = set_form.name.data
        if set_form.save.data:
            new_set = create_set(set_form, set_container)
            save_set_to_db(new_set, existing_set)
        if set_form.submit.data:
            new_set = create_set(set_form, set_container)
            new_set.status = 'running'
            save_set_to_db(new_set, existing_set)
            executed_set = ExecuteSet(
                id=new_set.id,
                status=new_set.status,
                temperature=new_set.temperature,
                timestamp=new_set.timestamp,
                container=set_container
            )
            execute_set(executed_set=executed_set)

    return render_set_template(set_form, set_container, all_containers)
