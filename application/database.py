from typing import Union
from pathlib import Path
from dotenv import dotenv_values
from psycopg2 import connect
from dataclasses import dataclass

parent_dir = Path(__file__).parent.parent
dotenv_dir = parent_dir / '.env'
dotenv_values = dotenv_values(dotenv_dir)


@dataclass
class ExecuteSet:
    __tablename__ = 'temp_set'
    id: str
    status: str
    temperature: int
    timestamp: int
    container: str


@dataclass
class ExecuteTask:
    __tablename__ = 'task'
    id: str
    start: int
    duration: int
    t_start: int
    t_min: int
    t_max: int
    t_freeze: int
    status: str
    container: str
    reads: list
    controls: list


def task_from_dict(t: dict) -> ExecuteTask:
    return ExecuteTask(
        id=t['id'],
        start=t['start'],
        duration=t['duration'],
        t_start=t['t_start'],
        t_min=t['t_min'],
        t_max=t['t_max'],
        t_freeze=t['t_freeze'],
        status=t['status'],
        container='',
        reads=list(),
        controls=list()
    )


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

    with select_connection:
        select_cursor.execute(select_query)
        values = select_cursor.fetchall()
        if not keys:
            return [val[0] for val in values]
        names = [description[0] for description in select_cursor.description]
        keyed_values = [dict(zip(names, row)) for row in values]

    return keyed_values


def update_status_in_db(update_object: object):
    insert_connection, insert_cursor = _db_connection_and_cursor()
    update_query = f"""
        UPDATE {update_object.__tablename__} SET status='{update_object.status}' WHERE id='{update_object.id}'
        """
    with insert_connection:
        insert_cursor.execute(update_query)
        insert_connection.commit()
