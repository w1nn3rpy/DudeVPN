import asyncio
import asyncpg
from create_bot import bot, dp, scheduler
from handlers.start import start_router
from keyboards.all_kb import set_commands
from decouple import config


# from work_time.time_func import send_time_msg


async def main():
    dp.include_router(start_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())


dp.include_router(start_router)
