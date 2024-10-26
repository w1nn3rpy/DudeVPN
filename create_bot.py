import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config

logging.basicConfig(
    filename='logs.log',
    filemode='w',
    level=logging.INFO,
    format='%(levelname)s %(filename)s: [%(asctime)s] - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S')
logger = logging.getLogger(__name__)

bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone='Europe/Samara')
