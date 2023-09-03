from flask import Blueprint, redirect, render_template
from .process import initialize_database, check_containers
from .models import Check, Container, Set
from . import db


control = Blueprint('control', __name__)


@control.route('/control')
def tasks():
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=(length := len(containers)),
        sets=Set.query.all(),
        checks={c.container: c for c in Check.query.order_by(Check.timestamp.desc()).limit(length)}
    )


@control.route("/control/initialize", methods=["POST"])
def init_db():
    initialize_database()
    return redirect('/control')


@control.route("/control/check", methods=["POST"])
def check():
    check_containers()
    return redirect('/control')

