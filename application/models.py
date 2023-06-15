from . import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))


class Container(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    given_name = db.Column(db.String(100))
    logged = db.Column(db.String(100))
    received = db.Column(db.String(100))
    power = db.Column(db.String(100))
    setpoint = db.Column(db.String(100))
    database_time = db.Column(db.String(100))

    measures = db.relationship("Thermometer", secondary="control_measure", back_populates="control")


class Thermometer(db.Model):
    __tablename__ = 'thermometer'
    device_id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100))
    temperature = db.Column(db.String(100))
    measure_time = db.Column(db.String(100))
    database_time = db.Column(db.String(100))

    control = db.relationship("Container", secondary="control_measure", back_populates="measures")

    def __str__(self):
        return self.device_name


db.Table(
    "control_measure",
    db.Column("control_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("measure_id", db.ForeignKey("thermometer.device_id"), primary_key=True)
)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    control = db.Column(db.String(100))
