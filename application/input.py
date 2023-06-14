from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms.fields import DateField, TimeField, SelectMultipleField, StringField, SubmitField
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


class ThermometerSelect(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class TaskForm(FlaskForm):
    given_name = StringField('given_name')
    measure_selection = ThermometerSelect('choices')


def render_task_template(
        all_containers: list[Container],
        task_container: Container,
        form: FlaskForm
    ):
    return render_template(
        "new_task.html",
        form=form,
        task_container=task_container,
        containers=all_containers,
    )


@input.route("/task/<string:container>", methods=["POST", "GET"])
def new_task(container: str):
    all_containers = Container.query.all()
    the_container = [cont for cont in all_containers if cont.name == container].pop()

    form = TaskForm(data={"choices": the_container.measures})
    form.measure_selection.choices = Thermometer.query.all()

    new_name = form.given_name.data
    new_selection = form.measure_selection.data
    print(new_name)
    if form.validate_on_submit():

        if new_name:
            the_container.given_name = new_name
        the_container.measures.clear()
        the_container.measures.extend(new_selection)
        db.session.commit()

    return render_task_template(
        form=form,
        all_containers=all_containers,
        task_container=the_container,
    )

