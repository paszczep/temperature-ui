from application.utility.database_connect import db_connection_and_cursor, database_exception
import logging
from typing import Union


@database_exception
def select_from_db(
        table_name: str,
        columns: Union[list, None] = None,
        where_condition: Union[dict, None] = None,
        keys: bool = True
) -> Union[list[str], list[dict]]:
    logging.info(f'select from db table {table_name}')

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

    select_query = f"""SELECT {col_str(columns)} FROM {table_name}{where_clause(where_condition)}"""
    select_connection, select_cursor = db_connection_and_cursor()

    with select_connection:
        select_cursor.execute(select_query)
        values = select_cursor.fetchall()
        if not keys:
            return_values = [val[0] for val in values]
        elif keys:
            names = [description[0] for description in select_cursor.description]
            return_values = [dict(zip(names, row)) for row in values]

    return return_values


@database_exception
def update_status_in_db(update_object: object):
    insert_connection, insert_cursor = db_connection_and_cursor()
    update_query = f"""
        UPDATE {update_object.__tablename__} SET status='{update_object.status}' WHERE id='{update_object.id}'
        """
    with insert_connection:
        insert_cursor.execute(update_query)
        insert_connection.commit()
