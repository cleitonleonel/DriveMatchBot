import re
import json
import requests
from datetime import datetime, timedelta

URL_BASE = 'https://www.google.com'


def add_minutes_to_current_time(minutes):
    current_time = datetime.now()
    time_delta = timedelta(minutes=minutes)
    new_time = current_time + time_delta

    return new_time


def get_full_address(lat, long):
    path_url = f"{URL_BASE}/maps/place/{lat},{long}"
    response = requests.get(path_url)
    html = response.text
    match = re.findall(r'window\.APP_INITIALIZATION_STATE=(.+?);', html)
    if match:
        data_str = match[0].strip().replace(")]}'", "")
        data = json.loads(data_str)
        full_address = data[9][1]
        return full_address

    return None


def get_coordinates(address):
    formatted_path = f"{address}".replace(" ", "+")
    path_url = f"{URL_BASE}/maps/place/{formatted_path}"
    response = requests.get(path_url)
    html = response.text
    match = re.findall(r'window\.APP_INITIALIZATION_STATE=(.+?);', html)
    if match:
        data_str = match[0].strip().replace(")]}'", "")
        padrao = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
        resultado = re.search(padrao, data_str)
        if resultado:
            latitude = resultado.group(1)
            longitude = resultado.group(2)
            return latitude, longitude
        return None, None

    return None, None


def get_address_info(origin, destination):
    formated_path = f"{origin}/{destination}".replace(" ", "+")
    path_url = f"{URL_BASE}/maps/dir/{formated_path}"
    try:
        response = requests.get(path_url)
        html = response.text
        match = re.findall(r'window\.APP_INITIALIZATION_STATE=(.+?);', html)
        if match:
            data_str = match[0].strip().replace(")]}'", "")
            data = json.loads(data_str)
            other_data = json.loads(data[3][4])
            distance_total = other_data[0][1][1][0][2][1]
            time_total = other_data[0][1][1][0][3][1]
            return {
                "url": path_url,
                "distance": distance_total,
                "time": time_total
            }
        return None
    except Exception as e:
        print(e)
        return None


def format_distance(distance_meters):
    if distance_meters >= 1000:
        distance_km = distance_meters / 1000
        return f"{distance_km:.2f} km"

    return f"{distance_meters} metros"


def reformat_distance(current_distance, additional_meters):
    number_str, unit = current_distance.split()
    number = float(number_str.replace(',', '.'))
    if unit == 'km':
        number *= 1000
    number += additional_meters
    if number >= 1000:
        number /= 1000
        unit = 'km'
    else:
        unit = 'metros'

    return f"{number:.1f} {unit}"


def update_time(original_time, additional_distance_meters):
    hours = 0
    minutes = 0
    parts = original_time.split()
    for i in range(len(parts)):
        if parts[i] == 'h':
            hours = int(parts[i-1])
        elif parts[i] == 'min':
            minutes = int(parts[i-1])

    total_minutes = hours * 60 + minutes
    if additional_distance_meters > 0:
        additional_time = additional_distance_meters / 250
        total_minutes += int(additional_time)

    updated_hours = total_minutes // 60
    updated_minutes = total_minutes % 60
    if updated_hours > 0:
        updated_time = f"{updated_hours} hrs {updated_minutes} min"
    else:
        updated_time = f"{updated_minutes} min"

    return updated_time
