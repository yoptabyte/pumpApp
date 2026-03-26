#!/usr/bin/env python3

import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.getenv('BOT_LOG_LEVEL', 'WARNING').upper(), logging.WARNING),
)
logger = logging.getLogger(__name__)


class BotConfig:
    def __init__(self) -> None:
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot_api_key = os.getenv('BOT_API_KEY')
        self.api_base_url = os.getenv('API_BASE_URL', 'http://web:8000')
        self.headers = {
            'Authorization': f'Api-Key {self.bot_api_key}',
            'Content-Type': 'application/json',
            'Host': os.getenv('HEADERS_HOST', 'web'),
        }
        self.validate_config()

    def validate_config(self) -> None:
        if not self.token:
            raise ValueError('TELEGRAM_BOT_TOKEN is not set')
        if not self.bot_api_key:
            raise ValueError('BOT_API_KEY is not set')


config = BotConfig()


def check_api_health() -> bool:
    try:
        response = requests.get(
            f'{config.api_base_url}/api/v1/health/',
            headers=config.headers,
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_training_sessions(chat_id: int) -> list[dict[str, str]]:
    try:
        response = requests.get(
            f'{config.api_base_url}/api/v1/bot/training-sessions/upcoming/',
            headers=config.headers,
            params={'telegram_user_id': str(chat_id)},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        logger.warning('Training sessions fetch failed')
        return []


def fetch_link_status(chat_id: int) -> dict[str, object]:
    try:
        response = requests.get(
            f'{config.api_base_url}/api/v1/bot/me/',
            headers=config.headers,
            params={'telegram_user_id': str(chat_id)},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        logger.warning('Telegram link status fetch failed')
        return {'linked': False, 'status': 'unavailable'}


def get_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton('Get training calendar')]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if not context.args:
        status = fetch_link_status(chat_id)
        if status.get('linked'):
            await update.message.reply_text(
                'Your Telegram account is already linked.',
                reply_markup=get_keyboard(),
            )
            sessions = fetch_training_sessions(chat_id)
            if sessions:
                await update.message.reply_text(format_training_sessions(sessions))
        else:
            await update.message.reply_text(
                'Your account is not linked with Telegram. Request a linking code on the website and scan the QR code.',
                reply_markup=get_keyboard(),
            )
        return

    linking_code = context.args[0]
    try:
        response = requests.post(
            f'{config.api_base_url}/api/v1/bot/telegram-link/confirm/',
            json={'code': linking_code, 'telegram_user_id': str(chat_id)},
            headers=config.headers,
            timeout=10,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        data = {'detail': 'Unable to link the account right now.'}
        response = None

    if response is not None and response.status_code == 200 and data.get('detail') == 'Telegram linked successfully.':
        await update.message.reply_text('Your account has been linked with Telegram.', reply_markup=get_keyboard())
        sessions = fetch_training_sessions(chat_id)
        if sessions:
            await update.message.reply_text(format_training_sessions(sessions))
        return

    await update.message.reply_text(
        f"Linking failed: {data.get('detail', 'Unknown error')}",
        reply_markup=get_keyboard(),
    )


async def handle_get_calendar(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    status = fetch_link_status(chat_id)
    if not status.get('linked'):
        await update.message.reply_text('Your account is not linked with Telegram. Use /start with your linking code.')
        return

    sessions = fetch_training_sessions(chat_id)
    if not sessions:
        await update.message.reply_text('You have no upcoming training sessions.')
        return

    await update.message.reply_text(format_training_sessions(sessions))


def format_training_sessions(sessions: list[dict[str, str]]) -> str:
    lines = ['Your training sessions:', '']
    for session in sessions:
        lines.append(f"Date: {session.get('date', 'N/A')}")
        lines.append(f"Time: {session.get('time', 'N/A')}")
        lines.append('')
    return '\n'.join(lines)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Bot update handling failed')
    if isinstance(update, Update) and update.effective_chat:
        await update.effective_chat.send_message('An internal error occurred. Please try again later.')


def main() -> None:
    application = Application.builder().token(config.token).build()
    application.add_handler(CommandHandler('start', handle_start))
    application.add_handler(MessageHandler(filters.Regex('^Get training calendar$'), handle_get_calendar))
    application.add_error_handler(error_handler)

    for _ in range(30):
        if check_api_health():
            break
        time.sleep(2)
    else:
        raise RuntimeError('API is not available after maximum retries')

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
