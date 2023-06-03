from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms.fields import DateTimeField
from wtforms.validators import DataRequired
from wtforms import widgets
from wtforms_alchemy import QuerySelectMultipleField
from .models import Container, Thermometer


input = Blueprint('input', __name__)


class QuerySelectMultipleFieldWithCheckboxes(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MyForm(FlaskForm):
    choices = QuerySelectMultipleFieldWithCheckboxes("Choices")


@input.route("task/<container_name>", methods=["POST", "GET"])
def index(parent_id):
    parent = Container.query.get(parent_id)
    form = MyForm(data={"choices": parent.children})
    form.choices.query = Thermometer.query.all()

    if form.validate_on_submit():
        parent.children.clear()
        parent.children.extend(form.choices.data)
        db.session.commit()

    return render_template("index.html", form=form)