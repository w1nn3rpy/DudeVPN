import asyncio
from datetime import datetime, timedelta

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
    """
    Удаление таблицы
    """
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        DROP TABLE {name}
        ''')
    await con.close()


async def add_promo(code: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        INSERT INTO promocodes(promo) VALUES ('{code}')
        ''')
    await con.close()


async def new_user(user_id: int, username: str = 'None', is_admin: bool = 'False', is_subscriber: bool = 'False'):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        INSERT INTO users(user_id, name, is_admin, is_subscriber) 
        VALUES ({user_id}, '{username}',{is_admin}, {is_subscriber})
        ''')
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


async def add_admin(user_id: int):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
    UPDATE users SET is_admin=True WHERE user_id = '{user_id}'
            ''')
    await con.close()


async def get_user_info(user_id: int, param: int = None):
    """
        1 - name str,
        2 - is_admin bool,
        3 - is_subscriber bool,
        4 - vpn_key str,
        5 - start_subscribe date,
        6 - end_subscribe date,
        7 - payment_label TEXT
    """
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    result = await con.fetchrow(f'''
        SELECT * FROM users WHERE user_id = '{user_id}'
                ''')
    await con.close()
    if result:
        if param:
            return result[param]
        return result
    return False


async def get_promo(code: str) -> bool:
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    result = await con.fetchrow(f'''
        SELECT promo FROM promocodes WHERE promo = '{code}'
                ''')
    if result:
        await con.execute(f'''
        delete FROM promocodes WHERE promo = '{code}'       
                ''')
        await con.close()
        return True
    await con.close()
    return False


async def add_label(user_id, label: str):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        UPDATE users SET payment_label='{label}' WHERE user_id = '{user_id}'
                ''')
    await con.close()


async def set_for_subscribe(user_id, buy_on):
    _today = datetime.date(datetime.now())
    _end_time = _today + timedelta(weeks=buy_on * 4)
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
            UPDATE users SET is_subscriber = True,
            start_subscribe = '{_today}',
            end_subscribe = '{_end_time} ', 
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
                WHERE user_id = {user_id}
                       ''')
    await con.close()


# asyncio.run(new_user(5983514379, 'w1nn3r1337'))

asyncio.run(set_for_subscribe(5983514379, 1))
_today = datetime.date(datetime.now())
_end_time = _today + timedelta(weeks=1 * 4)

