from flask import Blueprint, render_template
from flask_login import login_required
from application.utility.models_application import Container, Thermometer, Task, Check
from application.utility.form import TaskForm, timestamp_from_selection
from application.utility.process_tasking import thread_task
from application import db
from typing import Union
from uuid import uuid4
from humanize import naturaltime
from time import time
from datetime import datetime
from datetime import timedelta


input_task = Blueprint('input_task', __name__)


@input_task.route("/task/<container>", methods=["POST", "GET"])
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
            "t_start": old_task.t_start if old_task else 30,
            "t_max": old_task.t_max if old_task else 43,
            "t_min": old_task.t_min if old_task else 35,
            "t_freeze": old_task.t_freeze if old_task else 0
        }

    def render_task_form(
            render_form: TaskForm,
            render_container: Container,
            all_render_containers: list[Container],
            thermometer_names: dict,
            render_checks: Union[list[Check], None]
    ):
        now_time = time()
        return render_template(
            "task.html",
            form=render_form,
            task_container=render_container,
            all_containers=all_render_containers,
            status=render_container.task[0].status if render_container.task else None,
            reads=[{
                'temperature': r.temperature,
                'read_time': r.read_time,
                'db_time': naturaltime(timedelta(seconds=(now_time - r.db_time))),
                'thermometer': thermometer_names[r.thermometer]
            } for r in render_container.task[0].reads] if render_container.task else None,
            controls=[{
                'timestamp': naturaltime(timedelta(seconds=(now_time - ctrl.timestamp))),
                'temperature': ctrl.target_setpoint
            } for ctrl in render_container.task[0].controls] if render_container.task else None,
            checks=[{
                'set_point': c.read_setpoint,
                'timestamp': naturaltime(timedelta(seconds=(now_time - c.timestamp)))
            } for c in render_checks] if render_checks else None
        )

    def cancel_task(cancelled_task: Union[Task, None]):
        if cancelled_task:
            if cancelled_task.status in ('new', 'ended', 'cancelled', 'error'):
                db.session.delete(cancelled_task)
            elif cancelled_task.status == 'running':
                cancelled_task.status = 'cancelled'
            db.session.commit()

    def retrieve_relevant_checks(check_container: Container, check_task: Union[Task, None]) -> Union[list[Check], None]:
        if check_task:
            return db.session.query(Check).filter(
                Check.container == check_container.name).filter(
                Check.timestamp > check_task.start).order_by(Check.timestamp.desc()).all()

    def delete_old_task(del_task: Task):
        if del_task:
            db.session.delete(del_task)

    task_container = Container.query.get(container)
    all_containers = Container.query.all()
    existing_task = retrieve_task(task_container)
    form = TaskForm(data=form_data(task_container, existing_task))
    all_thermometers = Thermometer.query.all()
    form.choices.query = all_thermometers

    thermometer_map = {t.device_id: t.device_name for t in all_thermometers}
    checks = retrieve_relevant_checks(task_container, existing_task)

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

    return render_task_form(form, task_container, all_containers, thermometer_map, checks)
