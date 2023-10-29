from flask import Blueprint, redirect, render_template
from flask_login import login_required
from time import time
from humanize import naturaltime
from application.utility.launch import initialize_database, check_containers
from application.utility.models_application import (Check, Container, Set, data_objects, relationship_objects,
                                                    object_objects)
from application import db
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
    for relationship in relationship_objects:
        db.session.query(relationship).delete()

    for objects in data_objects:
        db.session.query(objects).delete()

    for things in object_objects:
        db.session.query(things).delete()

    db.session.commit()
    initialize_database()
    return redirect('/control')


@control.route("/control/delete", methods=["POST"])
@login_required
def delete_data():

    for relationship in relationship_objects:
        db.session.query(relationship).delete()

    for objects in data_objects:
        db.session.query(objects).delete()

    db.session.commit()
    return redirect('/control')


@control.route("/control/check", methods=["POST"])
@login_required
def check():
    Check.query.where(Check.timestamp < (int(time()) - 24*60*60)).delete()
    db.session.commit()
    check_containers()
    return redirect('/control')

