import asyncio

from create_bot import create_bot, logger
from handlers.admin_handlers import admin_router
from handlers.crypto_payment_handlers import crypto_payment_router
from handlers.start import start_router, set_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.db_users import check_end_subscribe
from database.models import create_table_if_not_exist
from handlers.common_payment_handlers import payment_router
from handlers.ruble_payment_handlers import ruble_payment_router
from handlers.stars_payment_handlers import stars_payment_router


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_end_subscribe, CronTrigger(hour=10), misfire_grace_time=180)
    scheduler.start()


async def main():
    await create_table_if_not_exist()

    bot, dp, client = await create_bot()

    # register routers AFTER dispatcher exists
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(payment_router)
    dp.include_router(ruble_payment_router)
    dp.include_router(stars_payment_router)
    dp.include_router(crypto_payment_router)

    start_scheduler()

    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands()

    try:
        await dp.start_polling(bot)

    finally:
        await bot.session.close()
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
