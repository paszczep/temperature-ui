from flask import Blueprint, render_template
from datetime import datetime
from .models import Container, Thermometer, Task
from .form import TaskForm
from . import db
from sqlalchemy import func


input = Blueprint('input', __name__)


@input.route('/task')
def tasks():
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=len(containers)
    )


def form_data(task_container: Container) -> dict:
    now = datetime.now()
    return {
        "name": task_container.label,
        "choices": task_container.thermometers,
        "date": now.date(),
        "time": now.time(),
        "hours": 6,
        "minutes": 0,
        "t_start": 40,
        "t_max": 35,
        "t_min": 30,
        "t_freeze": -20
    }

def start_timestamp_from_form(form: TaskForm) -> int:
    return int(datetime.timestamp(datetime.strptime(f'{form.date.data} {form.time.data}', '%Y-%m-%d %H:%M:%S')))


def create_task(form: TaskForm, task_container: Container) -> Task:
    id_0 = [t.id for t in Task.query.all()].pop() or 0
    return Task(id=id_0 + 1,
                start_timestamp=start_timestamp_from_form(form),
                duration=form.hours.data * 3600 + form.minutes.data * 60,
                t_start=form.t_start.data,
                t_min=form.t_min.data,
                t_max=form.t_max.data,
                t_freeze=form.t_freeze.data,
                status='new',
                container=task_container.name,
                )


@input.route("/task/<container>", methods=["POST", "GET"])
def task(container):
    task_container = Container.query.get(container)
    all_containers = Container.query.all()

    form = TaskForm(data=form_data(task_container))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        db.session.add(create_task(form, task_container))
        task_container.thermometers.clear()
        task_container.thermometers.extend(form.choices.data)
        task_container.label = form.name.data
        db.session.commit()

    return render_template(
        "task.html",
        form=form,
        task_container=task_container,
        all_containers=all_containers)
