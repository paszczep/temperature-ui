run_local:
	. venv/bin/activate
	export FLASK_APP="application"
	export FLASK_DEBUG=1
	flask run --host=0.0.0.0 --port=5000
db_init:
	. venv/bin/activate
	export FLASK_APP="application"
	flask db init
	flask db migrate
	flask db upgrade
build:
	docker build -t temp_ui .
launch:
	docker run -p 5000:5000 -t temp_ui
