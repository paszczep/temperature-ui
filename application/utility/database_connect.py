from psycopg2 import connect, OperationalError
from psycopg2.extensions import cursor, connection
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from dotenv import dotenv_values
import logging
from time import sleep

dotenv_path = Path(__file__).parent.parent.parent / '.env'
env_values = dotenv_values(dotenv_path)

db_config = {
    "host": env_values.get('DB_HOST'),
    "dbname": env_values.get('DB_NAME'),
    "user": env_values.get('DB_USER'),
    "password": env_values.get('DB_PASSWORD'),
    "port": env_values.get('DB_PORT')
}


def db_session():
    db_user = env_values.get('DB_USER')
    db_password = env_values.get('DB_PASSWORD')
    db_name = env_values.get('DB_NAME')
    db_host = env_values.get('DB_HOST')
    db_port = env_values.get('DB_PORT')

    db_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    engine = create_engine(db_uri)

    session = sessionmaker(bind=engine)
    return session()


CONNECTION_RETRIES = 10


def connection_generator(retries: int = CONNECTION_RETRIES):
    while retries:
        try:
            consecutive_connection = connect(**db_config)
            yield consecutive_connection
        except OperationalError as e:
            retries -= 1
            logging.warning(f"error connecting to database: {e}")
            sleep(3)
            continue
        finally:
            logging.info(f'db connection count {CONNECTION_RETRIES - retries + 1}')
    else:
        raise StopIteration


connection_gen = connection_generator()


def db_connection_and_cursor() -> tuple[connection, cursor]:
    for next_db_connection in connection_gen:
        try:
            next_db_cursor = next_db_connection.cursor()
            return next_db_connection, next_db_cursor
        except StopIteration:
            logging.warning("no working database connections available")
            raise ConnectionError


def database_exception(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logging.info(f"an error occurred: {e}")
        else:
            # info('no exceptions occurred')
            return result
        finally:
            logging.info("db cursor closed")
    return wrapper



