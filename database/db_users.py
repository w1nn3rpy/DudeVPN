import asyncpg

from database.db_servers import get_server_by_id, edit_server_active_users_count
from work_time.time_func import *
from create_bot import bot, logger
from outline.main import OutlineConnection
from database.models import DB_URL

async def new_user(user_id,
                   username: str = 'None'):
    con = None

    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
            INSERT INTO users(user_id, name) 
            VALUES ($1, $2)
            '''

        await con.execute(query, user_id, username)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def new_user_in_referral_system(user_id: int, referral_link, invited_by_id: int = None):
    con = None

    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        INSERT INTO referral_system (user_id, referral_link, invited_by_id)
        VALUES ($1, $2, $3)'''

        await con.execute(query, user_id, referral_link, invited_by_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def benefit_for_referral(referrer_id: int, referral_id: int):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        async with con.transaction():
            query = '''
            UPDATE referral_system 
            SET current_balance = current_balance + 50,
            total_earned = total_earned + 50,
            referral_count = referral_count + 1
            WHERE user_id = $1'''

            query_send_reward = '''
            UPDATE referral_system
            SET sent_reward_to_referrer = TRUE
            WHERE user_id = $1'''


            await con.execute(query, referrer_id)
            await con.execute(query_send_reward, referral_id)


    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def get_user_info(user_id):
    """
        1 - name str\n
        2 - is_admin bool\n
        3 - is_subscriber bool\n
        4 - vpn_key str\n
        5 - server_id int\n
        6 - start_subscribe date\n
        7 - end_subscribe date\n
        8 - trial_used bool\n
    """
    con = None

    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
            SELECT * 
            FROM users 
            WHERE user_id = $1
                    '''

        result = await con.fetchrow(query, user_id)

        return result

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_user_referral_system_by_id(user_id: int):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        user = await con.fetchrow(
            'SELECT * FROM referral_system WHERE user_id = $1', user_id)
        return user

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def pop_promo(code: str):

    con = None

    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        SELECT promo_code, duration 
        FROM promo_codes 
        WHERE promo_code = $1
                    '''

        result = await con.fetchrow(query, code)

        if result:
            query = '''
            DELETE FROM promo_codes 
            WHERE promo_code = $1       
                        '''

            await con.execute(query, code)

            return result
        return False

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def new_referral_balance_db(user_id: int, amount: int):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE referral_system
        SET current_balance = $1
        WHERE user_id = $2'''
        await con.execute(query, amount, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def set_for_subscribe(user_id, buy_on, server_id):
    """
    buy_on - кол-во дней подписки
    """

    start_time, end_time = get_time_for_subscribe(buy_on)
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users SET is_subscriber = True,
        start_subscribe = $1,
        end_subscribe = $2, 
        server_id = $3,
        trial_used = TRUE
        WHERE user_id = $4
               '''

        await con.execute(query, start_time, end_time, server_id, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def set_for_trial_subscribe(user_id, server_id):

    start_time, end_time = get_time_for_test_subscribe()
    con = None

    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users 
        SET is_subscriber = True,
        server_id = $1,
        start_subscribe = $2,
        end_subscribe = $3,
        trial_used = TRUE
        WHERE user_id = $4
               '''
        await con.execute(query, server_id, start_time, end_time, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def set_for_unsubscribe(user_id):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users 
        SET is_subscriber = False,
        vpn_key = null, 
        server_id = null,
        start_subscribe = null,
        end_subscribe = null
        WHERE user_id = $1
            '''
        await con.execute(query, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def set_user_vpn_key(user_id, key: str):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users 
        SET vpn_key = $1 
        WHERE user_id = $2
        '''

        await con.execute(query, key, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def update_username(user_id, username: str):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users 
        SET name = $1 
        WHERE user_id = $2
        '''

        await con.execute(query, username, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def check_end_subscribe():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)

        query_ended = """
                SELECT user_id, vpn_key, server_id
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
            try:
                await bot.send_message(user_id, f'‼️Уважаемый пользователь‼️\nВаша подписка закончится {end_subscribe}\n'
                                                'VPN ключ будет деактивирован.\n'
                                                'Для продления подписки введите команду /buy')
            except Exception as e:
                logger.error(f'Произошла ошибка оповещения юзера {user_id} о том, что его подписка скоро закончится: {e}')
                continue

        ended_sub_users = await con.fetch(query_ended, now)  # Нахождение пользователей с закончившейся подпиской

        for user in ended_sub_users:
            user_id = user['user_id']
            key = user['vpn_key']
            server_id = user['server_id']

            server_data = await get_server_by_id(server_id)
            outline_url = server_data['outline_url']
            outline_cert = server_data['outline_cert']

            client = OutlineConnection(outline_url, outline_cert)
            key_id = client.get_key_id_from_url(key)
            client.delete_key_method(key_id)
            await set_for_unsubscribe(user_id)
            await edit_server_active_users_count(server_id, 'sub')

            #TODO пофиксить убавление юзеров на сервере

            try:
                await bot.send_message(user_id, '‼️Уважаемый пользователь‼️\nВаша подписка закончилась.\n'
                                                'VPN ключ деактивирован.\n'
                                                'Для покупки нового ключа введите команду /buy')
            except Exception as e:
                logger.error(f'Произошла ошибка оповещения юзера {user_id} о том, что его подписка кончилась: {e}')
                continue

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_sub_ids():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = """
         SELECT user_id
         FROM users
         WHERE is_subscriber = True
         """
        ids = await con.fetch(query)
        return [record['user_id'] for record in ids]

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_all_ids():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = """
         SELECT user_id
         FROM users
         """
        ids = await con.fetch(query)
        return [record['user_id'] for record in ids]

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def add_balance_for_refer(to_user_id, by_user_id):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query_pay = """
        UPDATE users
        SET balance = balance + $1
        WHERE user_id = $2
        """

        await con.execute(query_pay, 25, to_user_id)

        query_set = """
        UPDATE users
        SET send_ref = TRUE
        WHERE user_id = $1
        """

        await con.execute(query_set, by_user_id)
        return True

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def extension_subscribe(user_id, amount_days: int):
    con = None

    try:
        con = await asyncpg.connect(DB_URL)
        get_query = """
        SELECT end_subscribe
        FROM users
        WHERE user_id = $1
        """
        end_sub_at_this_moment = await con.fetchval(get_query, user_id)

        new_end_subscribe = (end_sub_at_this_moment + timedelta(days=amount_days))

        set_query = """
        UPDATE users
        SET end_subscribe = $1
        WHERE user_id = $2
        """
        await con.execute(set_query, new_end_subscribe, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()