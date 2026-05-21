import asyncpg
from database.models import DB_URL
from create_bot import logger
from work_time.time_func import get_time_for_subscribe


async def add_promo(promo_code: str, duration: int):
    con = await asyncpg.connect(DB_URL)
    await con.execute(f'''
        INSERT INTO promo_codes(promo_code, duration) VALUES ($1, $2)
        ''', promo_code, duration)
    await con.close()


async def del_promo(promo_code: str):
    con = await asyncpg.connect(DB_URL)
    await con.execute(f'''
        DELETE FROM promo_codes WHERE promo_code = $1
        ''', promo_code)
    await con.close()


async def get_all_users():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        users = await con.fetch('SELECT * FROM users')
        return users

    except Exception as e:
        logger.error(f'Error in {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_all_subscribers():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        subs = await con.fetch('SELECT * FROM users WHERE is_subscriber = TRUE')
        return subs

    except Exception as e:
        logger.error(f'Error in {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_countries():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        countries = await con.fetch('SELECT * FROM countries')
        return countries

    except Exception as e:
        logger.error(f'Error in {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def extend_subscription(days: int, user_id: int | None = None):
    con = await asyncpg.connect(DB_URL)

    try:
        if user_id is None:
            query = """
                UPDATE users
                SET end_subscribe = end_subscribe + ($1::int * INTERVAL '1 day')
                WHERE is_subscriber = TRUE
            """
            return await con.execute(query, days)

        else:
            query = """
                UPDATE users
                SET end_subscribe = end_subscribe + ($1::int * INTERVAL '1 day')
                WHERE user_id = $2
            """
            return await con.execute(query, days, user_id)

    except Exception as e:
        logger.error(f'Error in {__name__}: {e}')

    finally:
        await con.close()