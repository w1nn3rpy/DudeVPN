import asyncio
from work_time.time_func import *

import asyncpg
from decouple import config


async def create_table():
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
    CREATE TABLE users(
        user_id INT8 PRIMARY KEY,
        name TEXT,
        is_admin bool,
        is_subscriber bool,
        vpn_key TEXT,
        start_subscribe date,
        end_subscribe date,
        payment_label TEXT)
    ''')
    await con.close()


async def drop_table(name: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        DROP TABLE {name}
        ''')
    await con.close()


async def add_promo(code: str, time: int):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        INSERT INTO promocodes(promo, time) VALUES ($1, $2)
        ''', code, time)
    await con.close()


async def del_promo(code: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        DELETE FROM promocodes WHERE promo = $1
        ''', code)
    await con.close()


async def new_user(user_id, username: str = 'None', is_admin=False, is_subscriber: bool = False):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        INSERT INTO users(user_id, name, is_admin, is_subscriber) 
        VALUES ($1, $2, $3, $4)
        ''', user_id, username, is_admin, is_subscriber)
    await con.close()


async def add_column(name_of_table: str, name_of_new_column: str, type_of_data: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        ALTER TABLE {name_of_table} ADD COLUMN {name_of_new_column} {type_of_data}'''
                      )
    await con.close()


async def change_column(name_of_table: str, column_name: str, type_of_data: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        ALTER TABLE {name_of_table} ALTER COLUMN {column_name} {type_of_data}'''
                      )
    await con.close()


async def add_admin(user_id):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
    UPDATE users SET is_admin=True WHERE user_id = $1
            ''', user_id)
    await con.close()


async def get_user_info(user_id, param: int = None):
    """
        1 - name str,
        2 - is_admin bool,
        3 - is_subscriber bool,
        4 - vpn_key str,
        5 - payment_label TEXT,
        6 - start_subscribe date,
        7 - end_subscribe date
    """
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    result = await con.fetchrow(f'''
        SELECT * FROM users WHERE user_id = $1
                ''', user_id)
    await con.close()
    if result:
        if param:
            return result[param]
        return result
    return False


async def pop_promo(code: str):
    sql_keywords = ['select', 'delete', 'insert', 'create', 'update', 'drop']
    for words in sql_keywords:
        if words in code.lower():
            return False

    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    result = await con.fetchrow(f'''
        SELECT promo, time FROM promocodes WHERE promo = $1
                ''', code)

    if result:
        await con.execute(f'''
        DELETE FROM promocodes WHERE promo = $1       
                ''', code)
        await con.close()
        return result
    await con.close()
    return False


async def add_label(user_id, label: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        UPDATE users SET payment_label = '{label}' WHERE user_id = '{user_id}'
                ''')
    await con.close()


async def set_for_subscribe(user_id, buy_on):
    start_time, end_time = get_time_for_subscribe(buy_on)

    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
            UPDATE users SET is_subscriber = True,
            start_subscribe = '{start_time}',
            end_subscribe = '{end_time} ', 
            payment_label = null 
            WHERE user_id = '{user_id}'
                   ''')
    await con.close()


async def set_for_unsubscribe(user_id):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
                UPDATE users SET is_subscriber = False,
                start_subscribe = null,
                end_subscribe = null
                WHERE user_id = '{user_id}'
                    ''')
    await con.close()


async def set_user_vpn_key(user_id, key: str):
    con = None
    try:
        con = await asyncpg.connect(dsn=config('DATABASE_URL'))
        await con.execute(f'''
        UPDATE users SET vpn_key = $1 WHERE user_id = $2 
                        ''', key, user_id)
    except Exception as e:
        print(str(e))
    finally:
        if con:
            await con.close()
