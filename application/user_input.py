from flask import Blueprint, render_template
from flask_login import login_required
from .models import Container, Thermometer, Task, Set, Check
from .form import TaskForm, SetForm
from .process import thread_task, thread_set, ExecuteSet
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


@user_input.route("/task/<container>", methods=["POST", "GET"])
@login_required
def task(container: str):
    def create_task(created_task_form: TaskForm) -> Task:
        return Task(
            id=str(uuid4()),
            start=timestamp_from_selection(created_task_form),
            duration=created_task_form.hours.data * 3600 + created_task_form.minutes.data * 60,
            t_start=created_task_form.t_start.data,
            t_min=created_task_form.t_min.data,
            t_max=created_task_form.t_max.data,
            t_freeze=created_task_form.t_freeze.data,
            status='new',
        )

    def retrieve_task(retrieved_task_container: Container) -> Union[Task, None]:
        old_task = retrieved_task_container.task
        return old_task[0] if old_task else None

    def create_task_settings(
            created_task_form: TaskForm,
            created_task_container: Container,
    ) -> Task:
        created_task = create_task(created_task_form)
        db.session.add(created_task)
        created_task_container.task.clear()
        created_task_container.task = [created_task]
        created_task_container.thermometers.clear()
        created_task_container.thermometers.extend(created_task_form.choices.data)
        created_task_container.label = created_task_form.name.data
        return created_task

    def form_data(tasked_container: Container, old_task: Union[Task, None]) -> dict:
        return {
            "name": tasked_container.label,
            "choices": tasked_container.thermometers,
            "date": (start := datetime.fromtimestamp(old_task.start)).date() if old_task else (
                now := datetime.now()).date(),
            "time": start.time() if old_task else now.time(),
            "hours": (hours := old_task.duration // 3600 if old_task else 1),
            "minutes": (old_task.duration - hours*3600) / 60 if old_task else 15,
            "t_start": old_task.t_start if old_task else 40,
            "t_max": old_task.t_max if old_task else 40,
            "t_min": old_task.t_min if old_task else 30,
            "t_freeze": old_task.t_freeze if old_task else -20
        }

    def render_task_form(
            render_form: TaskForm,
            render_container: Container,
            all_render_containers: list[Container]):
        return render_template(
            "task.html",
            form=render_form,
            task_container=render_container,
            all_containers=all_render_containers,
            status=render_container.task[0].status if render_container.task else None,
            reads=[{
                'temperature': r.temperature,
                'read_time': r.read_time,
                'db_time': naturaltime(timedelta(seconds=(time() - r.db_time)))
            } for r in render_container.task[0].reads] if render_container.task else None
        )

    def cancel_task(cancelled_task: Union[Task, None]):
        if cancelled_task:
            if cancelled_task.status in ('new', 'ended', 'cancelled'):
                db.session.delete(cancelled_task)
            elif cancelled_task.status == 'running':
                cancelled_task.status = 'cancelled'
            db.session.commit()

    def delete_old_task(del_task: Task):
        if del_task:
            db.session.delete(del_task)

    task_container = Container.query.get(container)
    all_containers = Container.query.all()
    existing_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, existing_task))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        if form.cancel.data:
            cancel_task(existing_task)
        if form.save.data:
            delete_old_task(existing_task)
            create_task_settings(form, task_container)
            db.session.commit()
        if form.submit.data:
            delete_old_task(existing_task)
            new_task = create_task_settings(form, task_container)
            new_task.status = 'running'
            db.session.commit()
            thread_task(new_task.id)

    return render_task_form(form, task_container, all_containers)


@user_input.route("/set/<container>", methods=["POST", "GET"])
@login_required
def temp_set(container):
    def retrieve_set(retrieve_set_container: Container) -> Union[Task, None]:
        old_set = retrieve_set_container.set
        return old_set[0] if old_set else None

    def save_set_to_db(created_set: Set, old_set: Union[Set, None]):
        if old_set:
            db.session.delete(old_set)
        db.session.add(created_set)
        db.session.commit()

    def create_set(creared_set_form: SetForm, created_set_container: Container) -> Set:
        return Set(
            id=str(uuid4()),
            status='new',
            temperature=creared_set_form.temperature.data,
            timestamp=timestamp_from_selection(creared_set_form),
            container=[created_set_container]
        )

    def cancel_set(cancelled_set: Union[Set, None]):
        if cancelled_set:
            if cancelled_set.status in ('new', 'ended', 'cancelled'):
                db.session.delete(cancelled_set)
            elif cancelled_set.status == 'running':
                cancelled_set.status = 'cancelled'
            db.session.commit()

    def set_data(target_container: Container, old_set: Union[Set, None]) -> dict:
        now = datetime.now()
        return {'name': target_container.label,
                'date': (set_datetime := datetime.fromtimestamp(old_set.timestamp)).date() if old_set else now.date(),
                'time': set_datetime.time() if old_set else now.time(),
                'temperature': old_set.temperature if old_set else 0
                }

    def retrieve_recent_container_check(checked_container: Container) -> Union[Check, None]:
        recent_container_check = db.session.query(Check).filter(
                Check.container == checked_container.name).order_by(
                Check.timestamp.desc()).first()
        return recent_container_check

    def render_set_template(
            rendered_set_form: SetForm,
            form_container: Container,
            rendered_all_containers: list[Container]):
        return render_template(
            "set.html",
            form=rendered_set_form,
            task_container=form_container,
            all_containers=rendered_all_containers,
            status=form_container.set[0].status if form_container.set else None,
            setpoint_check=retrieve_recent_container_check(form_container),
            controls=[{
                'timestamp': naturaltime(timedelta(seconds=(time() - ctrl.timestamp))),
                'temperature': ctrl.target_setpoint
            } for ctrl in form_container.set[0].controls] if form_container.set else None)

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
            thread_set(executed_set=executed_set)

    return render_set_template(set_form, set_container, all_containers)
