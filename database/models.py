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
                vpn_key TEXT DEFAULT NULL,
                server_id INT2 DEFAULT NULL,
                start_subscribe DATE DEFAULT NULL,
                end_subscribe DATE DEFAULT NULL,
                trial_used BOOLEAN DEFAULT FALSE
                )''',

            'promocodes': '''
            CREATE TABLE IF NOT EXISTS promo_codes(
                promo_code TEXT,
                duration INT4)
            ''',

            'servers': '''
            CREATE TABLE IF NOT EXISTS servers(
                server_id SERIAL PRIMARY KEY,
                country_id INT2,
                server_ip VARCHAR,
                server_password VARCHAR,
                outline_url VARCHAR,
                outline_cert VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                active_users INT4 DEFAULT 0,
                max_users INT4,
                vless_port INT4,
                manager_port INT4)
                ''',

            'countries': '''
            CREATE TABLE IF NOT EXISTS countries (
            id SERIAL PRIMARY KEY,
            code VARCHAR(3),
            name VARCHAR(255)
            );

            INSERT INTO countries (code, name) VALUES
            ('HU', '🇭🇺 Венгрия'),
            ('IL', '🇮🇱 Израиль'),
            ('UK', '🇬🇧 Англия'),
            ('DE', '🇩🇪 Германия'),
            ('PL', '🇵🇱 Польша'),
            ('USA', '🇺🇸 США'),
            ('FR', '🇫🇷 Франция'),
            ('CA', '🇨🇦 Канада'),
            ('KZ', '🇰🇿 Казахстан'),
            ('ES', '🇪🇸 Испания'),
            ('SE', '🇸🇪 Швеция'),
            ('PT', '🇵🇹 Португалия'),
            ('MD', '🇲🇩 Молдова'),
            ('LV', '🇱🇻 Латвия'),
            ('FI', '🇫🇮 Финляндия'),
            ('RU', '🇷🇺 Россия'),
            ('JP', '🇯🇵 Япония'),
            ('RO', '🇷🇴 Румыния'),
            ('AE', '🇦🇪 ОАЭ'),
            ('SG', '🇸🇬 Сингапур'),
            ('TR', '🇹🇷 Турция'),
            ('CZE', '🇨🇿 Чехия'),
            ('AU', '🇦🇺 Австралия'),
            ('ZA', '🇿🇦 ЮАР'),
            ('KR', '🇰🇷 Южная Корея'),
            ('AT', '🇦🇹 Австрия'),
            ('MX', '🇲🇽 Мексика'),
            ('DK', '🇩🇰 Дания'),
            ('IN', '🇮🇳 Индия'),
            ('NL', '🇳🇱 Нидерланды'),
            ('AR', '🇦🇷 Аргентина')
            ON CONFLICT DO NOTHING;
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
