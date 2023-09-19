#python3 venv . venv
#pip install -r requirements.txt
deactivate
source venv/bin/activate
source .env
export FLASK_APP="application"
#export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5000
