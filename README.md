*TEMPE_UI*
========

User interface service for Tempomat application setup guide.

## `.env` file

```
SECRET_KEY="..."

API_KEY_1="..."
API_KEY_2="..."

DB_USER="..."
DB_NAME="..."
DB_PASSWORD="..."
DB_PORT="..."
DB_HOST="..."

AWS_KEY_ID="..."
AWS_SECRET_KEY="..."

EMAIL_ADDRESS="..."
EMAIL_PASSWORD="..."
```
## Internal
`SECRET_KEY` refers to Flask Secret Key

## TEMPE_CTRL service connection

- `API_KEY_1` in *TEMPE_UI* equal to sha256 hash of `KEY_1` in *TEMPE_CTRL*
- `KEY_2` in *TEMPE_CTRL* equal to sha256 hash of `API_KEY_2` in *TEMPE_UI*
- `AWS_KEY_ID` `AWS_SECRET_KEY` belong to __AWS Lambda__ *TEMPE_CTRL* application

## Database

- `DB_` keys should point to a designated PostgresSQL Database

- migration:
```
export FLASK_APP="application"
flask db init
flask db migrate
flask db upgrade
```

## Application email

`EMAIL_` keys should belong to an application use enabled Gmail account

## First start

- To create superuser, access following URL, while replacing bolded values in curly brackets with what is appropriate

__{{APPLICATION_ADDRESS}}__/create_admin?pass=__{{ADMIN_PASS}}__&email=__{{ADMIN_EMAIL}}__

- Login as superuser to create designated user accounts.