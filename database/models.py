import asyncpg
from decouple import config

from create_bot import logger

DB_URL = config('DATABASE_URL')

async def create_table_if_not_exist():
    con = None
    try:
        con = await asyncpg.connect(DB_URL)
        tables = {
            'users': '''
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                name TEXT, 
                is_admin bool DEFAULT FALSE,
                is_subscriber bool DEFAULT FALSE, 
                sub_link TEXT DEFAULT NULL,
                remna_uuid TEXT DEFAULT NULL,
                start_subscribe DATE DEFAULT NULL,
                end_subscribe DATE DEFAULT NULL,
                trial_used BOOLEAN DEFAULT FALSE
                )''',

            'payments': '''
            CREATE TABLE IF NOT EXISTS payments(
            id SERIAL PRIMARY KEY,
            payment_id TEXT DEFAULT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            user_id BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            paid_at TIMESTAMPTZ DEFAULT NULL
                )''',

            'promocodes': '''
            CREATE TABLE IF NOT EXISTS promo_codes(
                promo_code TEXT,
                duration INT4)
            ''',

            'referral_system': '''
            CREATE TABLE IF NOT EXISTS referral_system (
            user_id BIGINT PRIMARY KEY,
            referral_link TEXT UNIQUE,
            current_balance INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            invited_by_id BIGINT DEFAULT NULL,
            referral_count INTEGER DEFAULT 0,
            is_advertiser BOOLEAN DEFAULT FALSE,
            got_from_adv BOOLEAN DEFAULT FALSE
            )'''
        }

        for table_name, create_sql in tables.items():
            table_exists = await con.fetchval(f"""
            SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = $1
                )
            """, table_name)
            if not table_exists:
                await con.execute(create_sql)
                logger.info(f'Table {table_name} successful created!')
            else:
                logger.info(f'Table {table_name} already exist!')

    finally:
        if con:
            await con.close()
