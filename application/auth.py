from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import AppUser
from . import db
from os import getenv

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
	return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
	email = request.form.get('email')
	password = request.form.get('password')
	remember = True if request.form.get('remember') else False

	user = AppUser.query.filter_by(email=email).first()

	if not user or not check_password_hash(user.password, password):
		flash('Check credentials')
		return redirect(url_for('auth.login'))

	login_user(user, remember=remember)
	return redirect(url_for('control.tasks'))


@auth.route('/signup')
@login_required
def signup():
	return render_template('signup.html')


@auth.route('/signup', methods=['POST'])
@login_required
def signup_post():
	email = request.form.get('email')
	name = request.form.get('name')
	password = request.form.get('password')

	user = AppUser.query.filter_by(
		email=email).first()

	if user:
		flash('Email address already exists')
		return redirect(url_for('auth.signup'))

	# create new user with the form data. Hash the password so plaintext version isn't saved.
	new_user = AppUser(email=email, name=name, password=generate_password_hash(password, method='sha256'))

	# add the new user to the database
	db.session.add(new_user)
	db.session.commit()

	return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('main.index'))


@auth.route('/create_admin')
def create_admin_user():
	email = request.args.get('email')
	name = 'superuser'
	password = request.args.get('pass')
	admin_user = AppUser.query.filter_by(
		admin=True).first()
	if not admin_user:
		new_user = AppUser(email=email, name=name, password=generate_password_hash(password, method='sha256'), admin=True)
		db.session.add(new_user)
		db.session.commit()
	return redirect(url_for('auth.login'))
