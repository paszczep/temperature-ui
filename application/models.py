from . import db
from flask_login import UserMixin


class AppUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    admin = db.Column(db.Boolean, default=False)


class Container(db.Model):
    """Controlled and Measured upon container"""
    name = db.Column(db.String(100), primary_key=True)
    label = db.Column(db.String(100))
    thermometers = db.relationship("Thermometer", secondary="container_thermometers", back_populates="container")
    task = db.relationship("Task", secondary="container_task", back_populates="container")
    set = db.relationship("Set", secondary="container_set", back_populates="container")


class Control(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    timestamp = db.Column(db.Integer)
    target_setpoint = db.Column(db.String(100))
    task = db.relationship("Task", secondary="task_controls", back_populates="controls")
    set = db.relationship("Set", secondary="set_controls", back_populates="controls")


class Check(db.Model):
    __tablename__ = 'container_check'
    id = db.Column(db.String(36), primary_key=True)
    container = db.Column(db.String(100))
    timestamp = db.Column(db.Integer)
    logged = db.Column(db.String(100))
    received = db.Column(db.String(100))
    power = db.Column(db.String(100))
    read_setpoint = db.Column(db.String(10))


class Thermometer(db.Model):
    """Measures temperature within Container during a Task"""
    __tablename__ = 'thermometer'
    device_id = db.Column(db.String(25), primary_key=True)
    device_name = db.Column(db.String(100))
    device_group = db.Column(db.String(100))
    container = db.relationship("Container", secondary="container_thermometers", back_populates="thermometers")

    def __str__(self):
        # return f'{self.device_group}'
        return f'{self.device_name}'


class Task(db.Model):
    """
    statuses: new, running, canceled, ended
    """
    id = db.Column(db.String(36), primary_key=True)
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
    """Thermometer read within a task"""
    __tablename__ = 'read'
    id = db.Column(db.String(36), primary_key=True)
    temperature = db.Column(db.String(10))
    read_time = db.Column(db.String(25))
    db_time = db.Column(db.Integer)
    thermometer = db.Column(db.String(10))
    task = db.relationship("Task", secondary="task_reads", back_populates="reads")


class Set(db.Model):
    __tablename__ = 'temp_set'
    id = db.Column(db.String(36), primary_key=True)
    status = db.Column(db.String(25))
    temperature = db.Column(db.String(10))
    timestamp = db.Column(db.Integer)
    container = db.relationship("Container", secondary="container_set", back_populates="set")
    controls = db.relationship("Control", secondary="set_controls", back_populates="set")


data_objects = (Control, Check, Task, Read, Set)


container_set = db.Table(
    "container_set",
    db.Column("container_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("set_id", db.ForeignKey("temp_set.id"), primary_key=True)
)

container_thermometers = db.Table(
    "container_thermometers",
    db.Column("container_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("thermometer_id", db.ForeignKey("thermometer.device_id"), primary_key=True)
)

container_task = db.Table(
    "container_task",
    db.Column("container_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("task_id", db.ForeignKey("task.id"), primary_key=True)
)

task_controls = db.Table(
    "task_controls",
    db.Column("task_id", db.ForeignKey("task.id"), primary_key=True),
    db.Column("control_id", db.ForeignKey("control.id"), primary_key=True)
)

set_controls = db.Table(
    "set_controls",
    db.Column("set_id", db.ForeignKey("temp_set.id"), primary_key=True),
    db.Column("control_id", db.ForeignKey("control.id"), primary_key=True)
)

task_reads = db.Table(
    "task_reads",
    db.Column("task_id", db.ForeignKey("task.id"), primary_key=True),
    db.Column("read_id", db.ForeignKey("read.id"), primary_key=True)
)

relationship_objects = [container_set, container_task, task_controls, set_controls, task_reads]
