source venv/bin/activate
source .env
#rm -fr migrations
export FLASK_APP="application"
flask db init
flask db migrate
flask db upgrade
