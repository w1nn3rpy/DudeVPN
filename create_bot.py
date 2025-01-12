import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config


file_handler = TimedRotatingFileHandler(
    filename='logs.log', when='midnight', interval=1, backupCount=7, encoding="utf-8"
)
console_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(filename)s:%(lineno)d: [%(asctime)s] - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
