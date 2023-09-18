#python3 venv . venv
#pip install -r requirements.txt
deactivate
source venv/bin/activate
source .env
export FLASK_APP="application"
export FLASK_DEBUG=1
flask run --port=8080
