source venv/bin/activate
source .env
rm -fr migrations
flask db init
flask db migrate
flask db upgrade
