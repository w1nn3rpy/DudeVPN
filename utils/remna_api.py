import aiohttp
from datetime import datetime, timedelta, timezone
from decouple import config


BASE_URL = config("REMNA_API_URL")
TOKEN = config("REMNA_API_TOKEN")
SQUAD_UUID = config("REMNA_SQUAD_UUID")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"

}

async def get_user_by_username(username: str):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(
            f"{BASE_URL}/users/by-username/{username}"
        ) as resp:

            if resp.status == 404:
                return None

            return await resp.json()

async def get_user_by_tg_id(telegram_id: str):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(
            f"{BASE_URL}/users/by-telegram-id/{telegram_id}"
        ) as resp:

            if resp.status != 200:
                return None

            return await resp.json()


async def create_user(
    telegram_id: int,
    days: int = 2,
):
    username = f"tg_{telegram_id}"

    expire_at = (
        datetime.now(timezone.utc) + timedelta(days=days)
    ).isoformat()

    payload = {
        "username": username,
        "expireAt": expire_at,
        "status": "ACTIVE",
        "telegramId": telegram_id,
        "activeInternalSquads": [SQUAD_UUID]
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(
                f"{BASE_URL}/users",
                json=payload
        ) as resp:
            data = await resp.json()

            return data

async def update_user(
    uuid: str,
    days: int
):
    expire_at = (
        datetime.now(timezone.utc) + timedelta(days=days)
    ).isoformat()

    payload = {
        "uuid": uuid,
        "expireAt": expire_at,
        "status": "ACTIVE"
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.patch(
            f"{BASE_URL}/users",
            json=payload
        ) as resp:

            return await resp.json()

async def get_or_create_subscription(
    telegram_id: int,
    days: int = 2,
):

    user = await get_user_by_tg_id(str(telegram_id))
    if user:
        print('user: ', user)
        user_data = user.get("response", user)
        if len(user_data) > 0:
            print('user_data: ', user_data)
            uuid = user_data[0].get("uuid")

            updated = await update_user(uuid, days)

            updated_data = updated.get("response", updated)

            return {
                "uuid": uuid,
                "sub_url": updated_data.get("subscriptionUrl")
            }

    created = await create_user(telegram_id, days)

    created_data = created.get("response", created)

    return {
        "uuid": created_data.get("uuid"),
        "sub_url": created_data.get("subscriptionUrl")
    }

async def bulk_extend_all_users(
    extend_days: int,
):
    payload = {
        "extendDays": extend_days
    }

    async with aiohttp.ClientSession(
        headers=HEADERS
    ) as session:

        async with session.post(
            f"{BASE_URL}/users/bulk/all/extend-expiration-date",
            json=payload
        ) as resp:

            if resp.status != 200:
                text = await resp.text()
                raise Exception(
                    f"Remna API error: {resp.status} {text}"
                )

            return await resp.json()