from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms.fields import DateField, TimeField, SelectMultipleField, StringField
from wtforms.validators import InputRequired, Length
from wtforms_alchemy import QuerySelectMultipleField, WeekDaysField
from wtforms import widgets
from datetime import datetime
from .models import Container, Thermometer
from . import db

input = Blueprint('input', __name__)


@input.route('/task')
def tasks():
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=len(containers)
    )


class NameChangeForm(FlaskForm):
    given_name = StringField('given_name')
    thermometer_select = SelectMultipleField('thermometer_select')


def render_task_template(
        all_containers: list[Container],
        task_container: Container,
        thermometers: list[Thermometer],
        form: FlaskForm
    ):
    return render_template(
        "new_task.html",
        form=form,
        task_container=task_container,
        containers=all_containers,
        thermometers=thermometers,
    )


@input.route("/task/<string:container>", methods=["POST", "GET"])
def new_task(container: str):
    all_containers = Container.query.all()

    the_container = [cont for cont in all_containers if cont.name == container].pop()
    all_thermometers = Thermometer.query.all()
    form = NameChangeForm()
    new_name = request.form.get('given_name')
    measures = request.form.get('thermometer_select')
    if form.validate_on_submit():
        if new_name:
            the_container.given_name = new_name
            db.session.commit()
        print(measures)

    return render_task_template(
        form=form,
        all_containers=all_containers,
        task_container=the_container,
        thermometers=all_thermometers
    )

