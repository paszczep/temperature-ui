from flask import Blueprint, redirect, render_template
from flask_login import login_required
from time import time
from .process import initialize_database, check_containers
from .models import Check, Container, Set
from . import db


control = Blueprint('control', __name__)


@control.route('/control')
@login_required
def tasks():
    return render_template(
        'control.html',
        containers=(containers := Container.query.all()),
        len=(length := len(containers)),
        sets=Set.query.all(),
        checks={c.container: c for c in Check.query.order_by(Check.timestamp.desc()).limit(length)}
    )


@control.route("/control/initialize", methods=["POST"])
@login_required
def init_db():
    initialize_database()
    return redirect('/control')


@control.route("/control/check", methods=["POST"])
@login_required
def check():
    Check.query.where(Check.timestamp < (int(time()) - 24*60*60)).delete()
    db.session.commit()
    check_containers()
    return redirect('/control')

