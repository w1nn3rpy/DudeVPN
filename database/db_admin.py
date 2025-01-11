import asyncpg
from database.models import DB_URL
from create_bot import logger

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


async def get_country_by_id(country_id):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        country = await con.fetchrow(
            'SELECT * FROM countries WHERE id = $1', country_id)
        return country

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_all_users():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        users = await con.fetch('SELECT * FROM users')
        return users

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

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
        logger.error(f'Ошибка в {__name__}: {e}')

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
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_country_by_code(code):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        country = await con.fetchrow('SELECT * FROM countries WHERE code = $1', code)
        return country

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def add_server(country_id, server_ip, server_password, outline_url, outline_cert, is_active, max_users, vless_port, manager_port):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        INSERT INTO servers (country_id, server_ip, server_password, outline_url, 
        outline_cert, is_active, max_users, vless_port, manager_port)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)'''
        await con.execute(query,country_id, server_ip, server_password,
                          outline_url, outline_cert, is_active, max_users, vless_port, manager_port)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()