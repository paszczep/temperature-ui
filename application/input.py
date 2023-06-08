from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms_alchemy import QuerySelectMultipleField
from wtforms import widgets
from .models import Container, Thermometer
from . import db

input = Blueprint('input', __name__)

@input.route('/task')
def tasks():
    containers = [container.__dict__ for container in Container.query.all()]
    return render_template(
        'control.html',
        containers=containers,
        len=len(containers)
    )


class QuerySelectMultipleFieldWithCheckboxes(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MyForm(FlaskForm):
    choices = QuerySelectMultipleFieldWithCheckboxes("Choices")


@input.route("/task/<container>", methods=["POST", "GET"])
def new_task(container):
    # container = str(container)[11:-1]
    parent = Container.query.get(container)
    print('!!!!!!', parent)
    form = MyForm(data={"choices": parent.children})
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        parent.children.clear()
        parent.children.extend(form.choices.data)
        db.session.commit()

    return render_template("task.html", form=form)

