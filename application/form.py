from flask_wtf import FlaskForm
from wtforms.fields import DateField, TimeField, StringField, SubmitField, IntegerField
from wtforms.validators import Length, InputRequired
from wtforms_alchemy import QuerySelectMultipleField
from wtforms import widgets


class QuerySelectMultipleFieldWithCheckboxes(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MinutesDelta(IntegerField):
    widget = widgets.NumberInput(step=15, min=0, max=45)


class HoursDelta(IntegerField):
    widget = widgets.NumberInput(step=1, min=0, max=48)


class TaskForm(FlaskForm):
    name = StringField('Name', validators=[Length(min=3, max=16)])
    choices = QuerySelectMultipleFieldWithCheckboxes("Choices")
    date = DateField('Date')
    time = TimeField('Time')
    minutes = MinutesDelta('Minutes')
    hours = HoursDelta('Hours')
    t_start = IntegerField('Start temperature')
    t_max = IntegerField('Max temperature')
    t_min = IntegerField('Min temperature')
    t_freeze = IntegerField('Freeze temperature')
    submit = SubmitField('Go!')


