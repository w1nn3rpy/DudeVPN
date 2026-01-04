import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(filename)s:%(lineno)d: [%(asctime)s] - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',
    handlers=[logging.StreamHandler(),
              logging.handlers.TimedRotatingFileHandler('/app/logs/logs.log', when='midnight',
                                                        interval=1, backupCount=7, encoding="utf-8")]
)
logger = logging.getLogger(__name__)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())