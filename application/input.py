from flask import Blueprint, render_template
from datetime import datetime
from .models import Container, Thermometer
from .form import TaskForm
from . import db

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
        "name": task_container.given_name,
        "choices": task_container.measures,
        "date": now.date(),
        "time": now.time(),
        "hours": 0,
        "minutes": 0,
        "t_start": 0,
        "t_max": 0,
        "t_freeze": 0
    }


@input.route("/task/<container>", methods=["POST", "GET"])
def task(container):
    task_container = Container.query.get(container)
    all_containers = Container.query.all()

    form = TaskForm(data=form_data(task_container))
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        task_container.measures.clear()
        task_container.measures.extend(form.choices.data)
        db.session.commit()

    return render_template(
        "task.html",
        form=form,
        task_container=task_container,
        all_containers=all_containers)
