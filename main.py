import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types
import logging
import json
import re

from auth_data import token
from weather import current_weather, weather_forecast


bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('logger')


@dp.message_handler(commands='start')
async def greeting(message: types.Message):
    await message.answer('<b>Привет!</b>\n'
                         'Я могу подсказать погоду\n'
                         'Для получения текущей погоды просто введи название города\n'
                         'Для получения прогноза набери "Прогноз (название города)"\n'
                         'Для включения рассылки набери "рассылка (название города) (время в формате HH:mm)"\n')


async def daily_send(chat_id, city):
    text = f'Пора вставать!\n' + weather_forecast(city)
    await bot.send_message(chat_id=chat_id, text=text)


async def scheduler():
    with open('daily_send.json', encoding='utf-8') as file:
        daily_send_list = json.load(file)
    for sending in daily_send_list:
        chat_id = sending['chat_id']
        send_time = sending['send_time']
        city = sending['city']
        aioschedule.every().day.at(send_time).do(daily_send, chat_id, city)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


@dp.message_handler()
async def send_weather(message: types.Message):

    user = f'{message.from_user["first_name"]} {message.from_user["last_name"]}'

    if 'прогноз' in message.text.lower():
        logger.info(f'{user} запросил прогноз погоды в {message.text.strip().split()[-1]}')
        await message.answer(f'{weather_forecast(message.text.strip().split()[-1])}')

    elif 'рассылка' in message.text.lower():
        city = message.text.lower().split()[1]
        send_time = message.text.lower().split()[2]
        chat_id = message['chat']['id']

        logger.info(f'{user} запросил рассылку погоды погоды в {city} в {send_time}')

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

            aioschedule.every().day.at(send_time).do(daily_send, chat_id, city)
            logger.info(f'Рассылка для пользователя {user} в {city} в {send_time} создана')
            await message.answer('Рассылка добавлена!')
        else:
            logger.error(f'Рассылка для пользователя {user} в {city} в {send_time} уже существует')
            await message.answer('Данная рассылка для Вас уже существует!')

    else:
        logger.info(f'{user} запросил текущую погоду в {message.text.strip()}')
        await message.answer(current_weather(message.text.strip()))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
