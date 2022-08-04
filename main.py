import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types, exceptions
import logging
import json
import re

from auth_data import token
from weather import current_weather, weather_forecast


bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('logger')


schedules = {}


@dp.message_handler(commands='start')
async def greeting(message: types.Message):
    await message.answer('<b>Привет!</b>\n'
                         'Я могу подсказать погоду\n'
                         'Для получения текущей погоды просто введи название города\n'
                         'Для получения прогноза набери "Прогноз (название города)"\n'
                         'Для включения рассылки набери "рассылка (название города) (время в формате HH:mm)"\n')


async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except exceptions.BotBlocked:
        logger.error(f'Отправка {chat_id} заблокирована пользователем.')
    except exceptions.ChatNotFound:
        logger.error(f'{chat_id} - Некорректный идентификатор пользователя.')
    except exceptions.UserDeactivated:
        logger.error(f'Пользователь {chat_id} деактивирован.')
    except exceptions.TelegramAPIError:
        logger.error(f'{chat_id} - ошибка отправки.')
    else:
        logger.info(f'Сообщение пользователю {chat_id} успешно отправлено.')
        return True
    return False



async def daily_send(chat_id, city):
    """
    Ежедневная отправка прогноза по расписанию.
    Принимает идентификатор пользователя и город,
    и отправляет прогноз.
    """
    text = f'Пора вставать!\n' + weather_forecast(city)
    await send_message(chat_id, text)


async def scheduler(schedules):

    # Загружаем список рассылок, оставшийся после предыдущего запуска,
    # и подключаем эти рассылки.
    with open('daily_send.json', encoding='utf-8') as file:
        daily_send_list = json.load(file)
    for sending in daily_send_list:
        chat_id = sending['chat_id']
        send_time = sending['send_time']
        city = sending['city']
        schedules[(chat_id, city, send_time)] = aioschedule.every().day.at(send_time).do(daily_send, chat_id, city)

    # Запускаем процесс рассылки.
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler(schedules))


async def send_forecast(chat_id, city):
    logger.info(f'{chat_id} запросил прогноз погоды в {city}')
    await send_message(chat_id, f'{weather_forecast(city)}')


async def send_current_weather(chat_id, city):
    logger.info(f'{chat_id} запросил текущую погоду в {city}')
    await send_message(chat_id, current_weather(city))


def get_command(text):
    try:
        command = text.strip().split()[0]
    except IndexError:
        return False, 'Пустая команда'

    if command.lower() in ('прогноз', 'forecast'):
        try:
            remaining_text = text.strip().split(maxsplit=1)[1]
        except IndexError:
            return False, 'Не указан город прогноза'
        return 'Forecast', remaining_text

    elif command.lower() in ('рассылка', 'schedule'):
        try:
            remaining_text = text.strip().split(maxsplit=1)[1]
        except IndexError:
            return False, 'Не указаны параметры рассылки'

        if len(remaining_text) < 2:
            return False, 'Недостаточно параметров рассылки'

        send_time = remaining_text.split()[-1]
        if not re.fullmatch('([0-9]|[01][0-9]|2[0-4]):([0-5][0-9])', send_time):
            return False, 'Некорректно указано время рассылки'

        return 'Schedule', remaining_text

    else:
        return 'Current', text


@dp.message_handler()
async def process_message(message: types.Message):
    chat_id = message.chat.id

    command, remaining_text = get_command(message.text)

    if command == 'Forecast':
        city = remaining_text
        logger.info(f'TARGET: {chat_id} - запросил прогноз погоды в {city}')
        await send_forecast(chat_id, city)

    elif command == 'Schedule':
        city = ' '.join(remaining_text.split()[:-1])
        send_time = remaining_text.split()[-1]

        logger.info(f'TARGET: {chat_id} - запросил рассылку погоды погоды в {city} в {send_time}')
        if current_weather(city) == 'Что-то пошло не так!':
            logger.error(f'TARGET: {chat_id} - не удалось проверить погоду по городу {city}.'
                         f' Вероятно, указано неверное название.')
            await send_message(chat_id, f'Не удается получить информацию по {city}.'
                                        f' Вероятно, указано неверное название.')
        else:
            with open('daily_send.json', encoding='utf-8') as file:
                daily_send_list = json.load(file)

            new_send_contact = {
                    'chat_id': chat_id,
                    'send_time': send_time,
                    'city': city,
                }

            if new_send_contact not in daily_send_list:
                daily_send_list.append(new_send_contact)
                with open('daily_send.json', 'w', encoding='utf-8') as file:
                    json.dump(daily_send_list, file, ensure_ascii=False, indent=4)

                schedules[(chat_id, city, send_time)] = aioschedule.every().day.at(send_time).do(daily_send,
                                                                                                 chat_id,
                                                                                                 city)
                logger.info(f'TARGET: {chat_id} - рассылка в {city} в {send_time} создана')
                await message.answer('Рассылка добавлена!')
            else:
                logger.error(f'TARGET: {chat_id} - рассылка в {city} в {send_time} уже существует')
                await message.answer('Данная рассылка для Вас уже существует!')

    elif command == 'Current':
        city = remaining_text
        await send_current_weather(chat_id, city)

    elif not command:
        logger.error(f'TARGET: {chat_id} - {remaining_text}')
        await send_message(chat_id, remaining_text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
