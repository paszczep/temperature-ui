from typing import Union
from pathlib import Path
from dotenv import dotenv_values
from psycopg2 import connect

parent_dir = Path(__file__).parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)


def _db_connection_and_cursor():
    db_config = {
        "host": dotenv_values.get('DB_HOST'),
        "dbname": dotenv_values.get('DB_NAME'),
        "user": dotenv_values.get('DB_USER'),
        "password": dotenv_values.get('DB_PASSWORD'),
        "port": dotenv_values.get('DB_PORT')
    }

    db_connection = connect(**db_config)
    db_cursor = db_connection.cursor()
    return db_connection, db_cursor


def select_from_db(
        table_name: str,
        select_columns: Union[list, None] = None,
        where_condition: Union[dict, None] = None,
        keys: bool = True
) -> Union[list, list[dict]]:

    def col_str(columns: list):
        if not columns:
            columns = '*'
        else:
            columns = str(columns)[1:-1].replace("'", '')
        return columns

    def where_clause(condition: dict) -> str:
        if condition:
            where_str = f" WHERE {list(condition.keys())[0]} = '{list(condition.values())[0]}'"
            return where_str
        else:
            return ''

    select_query = f"""SELECT {col_str(select_columns)} FROM {table_name}{where_clause(where_condition)}"""
    select_connection, select_cursor = _db_connection_and_cursor()

    with select_cursor:
        select_cursor.execute(select_query)
        values = select_cursor.fetchall()
        if not keys:
            return [val[0] for val in values]
        names = [description[0] for description in select_cursor.description]
        keyed_values = [dict(zip(names, row)) for row in values]

    return keyed_values