import asyncio
from create_bot import bot, dp
from handlers.start import start_router
from keyboards.all_kb import set_commands


async def main():
    dp.include_router(start_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands()
    await dp.start_polling(bot)

try:
    if __name__ == '__main__':
        asyncio.run(main())
except KeyboardInterrupt as e:
    print(str(e))
