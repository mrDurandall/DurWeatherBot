import requests
import json
import datetime


WIND_DIRECTIONS = {
    chr(8592): 'Восточный',
    chr(8593): 'Южный',
    chr(8594): 'Западный',
    chr(8595): 'Северный',
    chr(8598): 'Юго-Восточный',
    chr(8599): 'Юго-Западный',
    chr(8600): 'Северо-Западный',
    chr(8601): 'Северо-Восточный',
}

WWO_CODE = {
    "113": "Sunny",
    "116": "PartlyCloudy",
    "119": "Cloudy",
    "122": "VeryCloudy",
    "143": "Fog",
    "176": "LightShowers",
    "179": "LightSleetShowers",
    "182": "LightSleet",
    "185": "LightSleet",
    "200": "ThunderyShowers",
    "227": "LightSnow",
    "230": "HeavySnow",
    "248": "Fog",
    "260": "Fog",
    "263": "LightShowers",
    "266": "LightRain",
    "281": "LightSleet",
    "284": "LightSleet",
    "293": "LightRain",
    "296": "LightRain",
    "299": "HeavyShowers",
    "302": "HeavyRain",
    "305": "HeavyShowers",
    "308": "HeavyRain",
    "311": "LightSleet",
    "314": "LightSleet",
    "317": "LightSleet",
    "320": "LightSnow",
    "323": "LightSnowShowers",
    "326": "LightSnowShowers",
    "329": "HeavySnow",
    "332": "HeavySnow",
    "335": "HeavySnowShowers",
    "338": "HeavySnow",
    "350": "LightSleet",
    "353": "LightShowers",
    "356": "HeavyShowers",
    "359": "HeavyRain",
    "362": "LightSleetShowers",
    "365": "LightSleetShowers",
    "368": "LightSnowShowers",
    "371": "HeavySnowShowers",
    "374": "LightSleetShowers",
    "377": "LightSleet",
    "386": "ThunderyShowers",
    "389": "ThunderyHeavyRain",
    "392": "ThunderySnowShowers",
    "395": "HeavySnowShowers",
}

WEATHER_SYMBOL = {
    "Unknown":             "✨",
    "Cloudy":              "☁️",
    "Fog":                 "🌫",
    "HeavyRain":           "🌧",
    "HeavyShowers":        "🌧",
    "HeavySnow":           "❄️",
    "HeavySnowShowers":    "❄️",
    "LightRain":           "🌦",
    "LightShowers":        "🌦",
    "LightSleet":          "🌧",
    "LightSleetShowers":   "🌧",
    "LightSnow":           "🌨",
    "LightSnowShowers":    "🌨",
    "PartlyCloudy":        "⛅️",
    "Sunny":               "☀️",
    "ThunderyHeavyRain":   "🌩",
    "ThunderyShowers":     "⛈",
    "ThunderySnowShowers": "⛈",
    "VeryCloudy": "☁️",
}


def current_weather(city):

    headers = {
        'Accept-Language': 'ru'
    }

    url = f'https://wttr.in/{city}?format=j2'

    weather_json = requests.get(url, headers=headers)
    if weather_json.status_code == 404:
        return 'Что-то пошло не так!'
    weather = json.loads(weather_json.text)
    current_conditions = weather['current_condition'][0]

    weather_symbol = WEATHER_SYMBOL[WWO_CODE[current_conditions['weatherCode']]]

    answer_text = f'Текущая погода в {city}:\n' \
                  f'{weather_symbol} {current_conditions["lang_ru"][0]["value"]}\n' \
                  f'\n' \
                  f'🌡️ Температура воздуха: {current_conditions["temp_C"]}\n' \
                  f'🌡️ Ощущается как: {current_conditions["FeelsLikeC"]}\n' \
                  f'\n' \
                  f'🌬️ Ветер {current_conditions["winddir16Point"]} - {current_conditions["windspeedKmph"]} км/ч\n' \
                  f'\n'

    return answer_text


def weather_forecast(city):

    headers = {
        'Accept-Language': 'ru'
    }

    url = f'https://wttr.in/{city}?format=j1'

    weather_json = requests.get(url, headers=headers)
    if weather_json.status_code == 404:
        return 'Что-то пошло не так!'
    weather = json.loads(weather_json.text)
    forecast = weather['weather']
    forecast_by_hours = {}

    current_dt = datetime.datetime.now()

    for day in forecast:

        for time in day['hourly']:

            dt_for_hour = datetime.datetime(int(day['date'].split('-')[0]),
                                            int(day['date'].split('-')[1]),
                                            int(day['date'].split('-')[2]),
                                            hour=0+int(time['time'])//100)
            # forecast_by_hours[datetime.datetime(dt_for_hour)] = time
            forecast_by_hours.update({dt_for_hour: time})

    forecast_text = f'Прогноз погоды в {city} на ближайшие сутки:\n' \
                    f'-------------------------------------------\n'

    counter = 0
    for fore_time in forecast_by_hours:
        if counter == 9:
            break
        if fore_time > current_dt:
            conditions = forecast_by_hours[fore_time]
            weather_symbol = WEATHER_SYMBOL[WWO_CODE[conditions['weatherCode']]]

            forecast_text += f'<b>{fore_time}</b>:\n' \
                             f'{weather_symbol} {conditions["lang_ru"][0]["value"]}\n' \
                             f'🌡️ Температура воздуха: {conditions["tempC"]} °C\n' \
                             f'🌡️ Ощущается как: {conditions["FeelsLikeC"]} °C\n' \
                             f'🌬️ Ветер {conditions["winddir16Point"]} - {conditions["windspeedKmph"]} км/ч\n' \
                             f'💧 Вероятность дождя {conditions["chanceofrain"]}\n' \
                             f'\n'
            counter += 1

    return forecast_text


if __name__ == '__main__':

    # print(current_weather('Северодвинск'))
    print(weather_forecast('Северодвинск'))



