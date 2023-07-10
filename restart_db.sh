conda activate temp_ui --stack
source .env
rm -fr migrations instance
flask db init
flask db migrate
flask db upgrade
