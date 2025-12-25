import asyncpg
from database.models import DB_URL
from create_bot import logger

async def get_all_servers():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        servers = await con.fetch('SELECT * FROM servers ORDER BY server_id')
        return servers

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_server_with_min_user_ratio_by_country(country_id):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        SELECT server_id, outline_url, outline_cert, active_users, max_users,
        (CAST(active_users AS FLOAT) / max_users) AS user_ratio
        FROM servers
        WHERE max_users > 0 AND country_id = $1
        ORDER BY user_ratio ASC
        LIMIT 1;
        '''

        result = await con.fetchrow(query, country_id)

        return result

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()


async def get_random_server_with_min_user_ratio():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        SELECT server_id, outline_url, outline_cert, is_active, active_users, max_users,
        (CAST(active_users AS FLOAT) / max_users) AS user_ratio
        FROM servers
        WHERE max_users > 0 AND is_active = TRUE
        ORDER BY user_ratio ASC
        LIMIT 1;
        '''

        result = await con.fetchrow(query)

        return result

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def edit_server_active_users_count(server_id, action: str):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)

        query_add = '''
        UPDATE servers SET active_users = active_users + 1
        WHERE server_id = $1'''

        query_sub = '''
        UPDATE servers SET active_users = active_users - 1
        WHERE server_id = $1'''

        if action == 'add':
            await con.execute(query_add, server_id)
        elif action == 'sub':
            await con.execute(query_sub, server_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_locations_of_active_servers():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        async with con.transaction():
            get_locations_query = '''
            SELECT DISTINCT c.id AS country_id, c.name AS country_name
            FROM servers s
            INNER JOIN countries c ON s.country_id = c.id
            WHERE s.is_active = TRUE
            '''

            locations = await con.fetch(get_locations_query)
            return {str(record['country_id']): record['country_name'] for record in locations}

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def get_server_by_id(server_id):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        server = await con.fetchrow(
            'SELECT * FROM servers WHERE server_id = $1', server_id)
        return server

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()

async def check_server_not_full(server_id):
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        query = '''
        SELECT active_users, max_users
        FROM servers
        WHERE server_id = $1'''

        result = await con.fetchrow(query, server_id)

        return result

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if con:
            await con.close()