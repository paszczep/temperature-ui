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

    children = db.relationship("Thermometer", secondary="container_thermometer", back_populates="parents")


class Thermometer(db.Model):
    device_id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100))
    temperature = db.Column(db.String(100))
    measure_time = db.Column(db.String(100))
    database_time = db.Column(db.String(100))

    parents = db.relationship("Container", secondary="container_thermometer", back_populates="children")

    def __str__(self):
        return f"{self.device_name} {self.temperature}"


db.Table(
    "container_thermometer",
    db.Column("parent_id", db.ForeignKey("container.name"), primary_key=True),
    db.Column("child_id", db.ForeignKey("thermometer.device_id"), primary_key=True)
)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
