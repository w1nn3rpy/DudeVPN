import time

from work_time.time_func import *

import asyncpg
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from create_bot import bot
from outline.main import get_key_id_from_url, delete_key


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
        if param is not None:
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


async def del_label(user_id):
    con = await asyncpg.connect(dsn=config('DATABASE_URL'))
    await con.execute(f'''
        UPDATE users SET payment_label = null WHERE user_id = '{user_id}'
                ''')
    await con.close()


async def set_for_subscribe(user_id, buy_on):
    """
    buy_on - кол-во недель подписки
    """
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
                vpn_key = null, 
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


async def update_username(user_id, username: str):
    con = None
    try:
        con = await asyncpg.connect(dsn=config('DATABASE_URL'))
        await con.execute(f'''
        UPDATE users SET name = $1 WHERE user_id = $2 
                        ''', username, user_id)
    except Exception as e:
        print(str(e))
    finally:
        if con:
            await con.close()


async def check_end_subscribe():
    con = None
    try:
        con = await asyncpg.connect(dsn=config('DATABASE_URL'))

        query_ended = """
                SELECT user_id, vpn_key
                FROM users
                WHERE end_subscribe <= $1
                """
        query_end_soon = """
                SELECT user_id, end_subscribe
                FROM users
                WHERE end_subscribe < $1 AND end_subscribe >= $2
                """
        now = datetime.now()  # Сегодняшняя дата
        later3days = now + timedelta(days=3)
        later2days = now + timedelta(days=2)
        end_soon_users = await con.fetch(query_end_soon, later3days, later2days)

        for user in end_soon_users:
            user_id = user['user_id']
            end_subscribe = user['end_subscribe']
            await bot.send_message(user_id, f'‼️Уважаемый пользователь‼️\nВаша подписка закончится {end_subscribe}\n'
                                            'VPN ключ будет деактивирован.\n'
                                            'Для покупки нового ключа введите команду /buy')

        ended_sub_users = await con.fetch(query_ended, now)  # Нахождение пользователей с закончившейся подпиской

        for user in ended_sub_users:
            user_id = user['user_id']
            key = user['vpn_key']
            await bot.send_message(user_id, '‼️Уважаемый пользователь‼️\nВаша подписка закончилась.\n'
                                            'VPN ключ деактивирован.\n'
                                            'Для покупки нового ключа введите команду /buy')
            key_id = await get_key_id_from_url(key)
            await delete_key(key_id)
            await set_for_unsubscribe(user_id)

    except Exception as e:
        print(str(e))

    finally:
        await con.close()
