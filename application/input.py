from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms.fields import DateField, TimeField, SelectMultipleField, StringField, SubmitField, IntegerField
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


class QuerySelectMultipleFieldWithCheckboxes(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MinutesDelta(IntegerField):
    widget = widgets.NumberInput(step=15, min=0, max=45)


class HoursDelta(IntegerField):
    widget = widgets.NumberInput(step=1, min=0, max=24)


class MyForm(FlaskForm):
    name = StringField('Name')
    choices = QuerySelectMultipleFieldWithCheckboxes("Choices")
    date = DateField('Date')
    time = TimeField('Time')
    minutes = MinutesDelta('Minutes')
    hours = HoursDelta('Hours')
    temperature = IntegerField('Temperature')
    submit = SubmitField('Go!')


@input.route("/task/<container>", methods=["POST", "GET"])
def task(container):
    task_container = Container.query.get(container)
    all_containers = Container.query.all()

    now = datetime.now()

    data = {
        "name": task_container.given_name,
        "choices": task_container.measures,
        "date": now.date(),
        "time": now.time(),
        "hours": 0,
        "minutes": 0,
        "temperature": 0
    }

    form = MyForm(data=data)
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
