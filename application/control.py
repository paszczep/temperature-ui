from flask import Blueprint, redirect, render_template
from flask_login import login_required
from time import time
from humanize import naturaltime
from .process import initialize_database, run_lambda
from .models import Check, Container, Set, Task, Read, Control
from . import db
from datetime import timedelta

control = Blueprint('control', __name__)


@control.route('/control')
@login_required
def tasks():
    containers = Container.query.all()
    length = len(containers)
    checks = Check.query.order_by(Check.timestamp.desc()).limit(length).all()
    keyed_checks = {}
    refresh = int()
    if checks:
        refresh = max(int(c.timestamp) for c in checks)
        keyed_checks = {c.container: c for c in checks if c.timestamp == refresh}
        refresh = naturaltime(timedelta(seconds=(time() - refresh)))
    return render_template(
        'control.html',
        containers=containers,
        len=length,
        sets=Set.query.all(),
        checks=keyed_checks,
        refresh=refresh
    )


@control.route("/control/initialize", methods=["POST"])
@login_required
def init_db():
    initialize_database()
    return redirect('/control')


@control.route("/control/delete", methods=["POST"])
@login_required
def delete_checks():
    db.session.query(Check).delete()
    db.session.query(Set).delete()
    db.session.query(Task).delete()
    db.session.query(Read).delete()
    db.session.query(Control).delete()

    db.session.commit()
    return redirect('/control')


@control.route("/control/check", methods=["POST"])
@login_required
def check():
    Check.query.where(Check.timestamp < (int(time()) - 24*60*60)).delete()
    db.session.commit()
    run_lambda(check=True)
    return redirect('/control')

