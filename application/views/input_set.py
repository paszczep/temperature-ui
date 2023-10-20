from flask import Blueprint, render_template
from flask_login import login_required
from application.utility.models import Container, Set, Check
from application.utility.form import SetForm, timestamp_from_selection
from application.utility.process_setting import thread_set, ExecuteSet
from application import db
from typing import Union
from uuid import uuid4
from humanize import naturaltime
from time import time
from datetime import datetime
from datetime import timedelta


input_set = Blueprint('input_set', __name__)


@input_set.route("/set/<container>", methods=["POST", "GET"])
@login_required
def temp_set(container):
    def retrieve_set(retrieve_set_container: Container) -> Union[Set, None]:
        old_set = retrieve_set_container.set
        return old_set[0] if old_set else None

    def save_set_to_db(created_set: Set, old_set: Union[Set, None]):
        if old_set:
            db.session.delete(old_set)
        db.session.add(created_set)
        db.session.commit()

    def create_set(created_set_form: SetForm, created_set_container: Container) -> Set:
        return Set(
            id=str(uuid4()),
            status='new',
            temperature=created_set_form.temperature.data,
            timestamp=timestamp_from_selection(created_set_form),
            container=[created_set_container]
        )

    def cancel_set(cancelled_set: Union[Set, None]):
        if cancelled_set:
            if cancelled_set.status in ('new', 'ended', 'cancelled', 'error'):
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
            rendered_all_containers: list[Container],
            render_checks
    ):
        now_time = time()
        return render_template(
            "set.html",
            form=rendered_set_form,
            task_container=form_container,
            all_containers=rendered_all_containers,
            status=form_container.set[0].status if form_container.set else None,
            setpoint_check=retrieve_recent_container_check(form_container),
            controls=[{
                'timestamp': naturaltime(timedelta(seconds=(now_time - ctrl.timestamp))),
                'temperature': ctrl.target_setpoint
            } for ctrl in form_container.set[0].controls] if form_container.set else None,
            checks=[{
                'set_point': c.read_setpoint,
                'timestamp': naturaltime(timedelta(seconds=(now_time - c.timestamp)))
            } for c in render_checks] if render_checks else None
        )

    def retrieve_relevant_checks(check_container: Container, check_set: Union[Set, None]) -> Union[list[Check], None]:
        if check_set:
            return db.session.query(Check).filter(
                Check.container == check_container.name).filter(
                Check.timestamp > check_set.timestamp).order_by(Check.timestamp.desc()).all()

    set_container = Container.query.get(container)
    all_containers = Container.query.all()
    existing_set = retrieve_set(set_container)
    set_form = SetForm(data=set_data(set_container, existing_set))
    checks = retrieve_relevant_checks(set_container, existing_set)

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

    return render_set_template(set_form, set_container, all_containers, checks)
