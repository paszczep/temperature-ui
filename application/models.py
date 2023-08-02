from . import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))


class Container(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    label = db.Column(db.String(100))
    thermometers = db.relationship("Thermometer", secondary="container_thermometers", back_populates="container")
    task = db.relationship("Task", secondary="container_task", back_populates="container")


class Control(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100))  # check or set
    timestamp = db.Column(db.Integer)
    logged = db.Column(db.String(100))
    received = db.Column(db.String(100))
    power = db.Column(db.String(100))
    target_setpoint = db.Column(db.String(100))
    read_setpoint = db.Column(db.String(10))
    task = db.relationship("Task", secondary="task_controls", back_populates="controls")


class Thermometer(db.Model):
    __tablename__ = 'thermometer'
    device_id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100))
    container = db.relationship("Container", secondary="container_thermometers", back_populates="thermometers")

    def __str__(self):
        return self.device_name


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    t_start = db.Column(db.Integer)
    t_min = db.Column(db.Integer)
    t_max = db.Column(db.Integer)
    t_freeze = db.Column(db.Integer)
    status = db.Column(db.String(25))
    container = db.relationship("Container", secondary="container_task", back_populates="task")
    reads = db.relationship("Read", secondary="task_reads", back_populates="task")
    controls = db.relationship("Control", secondary="task_controls", back_populates="task")


class Read(db.Model):
    __tablename__ = 'read'
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.String(10))
    read_time = db.Column(db.String(100))
    db_time = db.Column(db.String(100))
    thermometer = db.Column(db.Integer)
    task = db.relationship("Task", secondary="task_reads", back_populates="reads")


class Set(db.Model):
    __tablename___ = 'set'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(25))
    temperature = db.Column(db.String(10))
    timestamp = db.Column(db.Integer)
    container = db.Column(db.String(100))


db.Table(
    "container_thermometers",
    db.Column("container_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("thermometer_id", db.ForeignKey("thermometer.device_id"), primary_key=True)
)


db.Table(
    "container_task",
    db.Column("container_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("task_id", db.ForeignKey("task.id"), primary_key=True)
)


db.Table(
    "task_controls",
    db.Column("task_id", db.ForeignKey("task.id"), primary_key=True),
    db.Column("control_id", db.ForeignKey("control.id"), primary_key=True)
)


db.Table(
    "task_reads",
    db.Column("task_id", db.ForeignKey("task.id"), primary_key=True),
    db.Column("read_id", db.ForeignKey("read.id"), primary_key=True)
)
