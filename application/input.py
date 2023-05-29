from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms.validators import DataRequired
from wtforms import validators, SubmitField


input = Blueprint('input', __name__)

class InfoForm(FlaskForm):
    startdate = DateField('Start Date')