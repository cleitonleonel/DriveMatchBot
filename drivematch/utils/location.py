import re
import json
import logging
from datetime import datetime, timedelta
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from drivematch.utils.navigator import Browser

_geolocator = Nominatim(user_agent="drivematch_bot/1.0", timeout=10)

URL_BASE = 'https://www.google.com'

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "downlink": "6.9",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "rtt": "50",
    "sec-ch-prefers-color-scheme": "dark",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-arch": "\"x86\"",
    "sec-ch-ua-bitness": "\"64\"",
    "sec-ch-ua-full-version-list": "\"Not(A:Brand\";v=\"99.0.0.0\", \"Google Chrome\";v=\"133.0.6943.53\", \"Chromium\";v=\"133.0.6943.53\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "\"\"",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-ch-ua-platform-version": "\"6.8.0\"",
    "sec-ch-ua-wow64": "?0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "x-browser-channel": "stable",
    "x-browser-copyright": "Copyright 2025 Google LLC. All rights reserved.",
    "x-browser-validation": "jZdx9KTcf3xZTA6lwngDjRloSWY=",
    "x-browser-year": "2025"
}

browser = Browser()
browser.set_headers(headers)


def add_minutes_to_current_time(minutes):
    current_time = datetime.now()
    time_delta = timedelta(minutes=minutes)
    new_time = current_time + time_delta

    return new_time


def clean_address(address_str):
    """Remove termos irrelevantes e verbosidades do endereço do Nominatim."""
    if not address_str:
        return ""

    # Remover termos comuns que poluem o Nominatim no Brasil
    replacements = [
        r", Região Geográfica [^,]+",
        r", Região Metropolitana [^,]+",
        r", Região Intermediária [^,]+",
        r", Microrregião [^,]+",
        r", Mesorregião [^,]+",
        r", Brasil$",
    ]
    for pattern in replacements:
        address_str = re.sub(pattern, "", address_str)

    # Limpar espaços extras
    parts = [p.strip() for p in address_str.split(',') if p.strip()]

    # Priorizar: Logradouro, Número (se existir), Bairro, Cidade
    # O Nominatim costuma vir: [Logradouro], [Número], [Bairro], [Cidade], [Estado], [CEP]
    if len(parts) > 4:
        # Tenta pegar apenas as 4 primeiras partes relevantes
        return ", ".join(parts[:4])

    return ", ".join(parts)


def reverse_geocode_gmaps(lat, long):
    """Obtém endereço limpo via scraper do Google Search/Maps."""
    try:
        path_url = (
            f"{URL_BASE}/maps/preview/reveal?authuser=0&hl=pt-BR&gl=br&pb=!"
            f"2m12!1m3!1d20.9!2d{long}!3d{lat}!2m3!1f0!2f0!3f0!3m2!1i1366!2i358!"
            f"4f13.1!3m2!2d{long}!3d{lat}!4m2!1sbE!7e81!5m5!2m4!1i800!2i600!3i1!4i8"
        )
        response = browser.send_request("GET", path_url)
        json_str = response.text.replace(")]}'", "").strip()
        data = json.loads(json_str)
        return ', '.join(data[0])
    except Exception as e:
        logging.warning(f"GMaps scraper error: {e}")
    return None


def get_full_address(lat, long):
    """Obtém endereço completo com prioridade para Scraper e Fallback para Nominatim limpo."""
    # 1. Tentar Scraper do Google (Mais fiel e preciso)
    gmaps_address = reverse_geocode_gmaps(lat, long)
    if gmaps_address:
        logging.info(f"Endereço obtido via GMaps Scraper: {gmaps_address}")
        return gmaps_address

    # 2. Fallback Nominatim (Com limpeza rigorosa)
    try:
        location = _geolocator.reverse((lat, long), language='pt-BR')
        if location:
            full_address = location.address
            cleaned = clean_address(full_address)
            logging.info(f"Endereço obtido via Nominatim (Limpo): {cleaned}")
            return cleaned
    except Exception as e:
        logging.warning(f"Nominatim reverse error: {e}")

    return f"{lat}, {long}"


def geocode_gmaps(address):
    """Obtém coordenadas a partir de um endereço usando scraper do Google Search."""
    try:
        formatted_path = f"{address}".replace(" ", "+")
        path_url = f"{URL_BASE}/maps/place/{formatted_path}"
        browser.send_request("GET", path_url)
        path_url = f"{URL_BASE}{browser.get_soup().find("link")["href"]}"
        response = browser.send_request("GET", path_url)
        json_str = response.text.replace(")]}'", "").strip()
        match = re.findall(r'\[null,null,(-?\d+\.\d+),(-?\d+\.\d+)]', json_str)
        if match:
            return match[1]
        return None, None
    except Exception as e:
        logging.warning(f"GMaps geocode scraper error: {e}")
    return None, None


def get_coordinates(address):
    """Obtém coordenadas a partir de um endereço com prioridade para Scraper e Fallback para Nominatim."""
    # 1. Tentar Scraper do Google
    lat, lon = geocode_gmaps(address)
    if lat and lon:
        return lat, lon

    # 2. Fallback Nominatim
    try:
        location = _geolocator.geocode(address, language='pt-BR')
        if location:
            logging.info(
                f"Coordenadas encontradas via Nominatim para '{address}': {location.latitude}, {location.longitude}")
            return str(location.latitude), str(location.longitude)
    except Exception as e:
        logging.warning(f"Nominatim geocode error for '{address}': {e}")
    return None, None


def get_address_info(origin, destination):
    import requests
    formated_path = f"{origin}/{destination}".replace(" ", "+")
    direction_url = f"{URL_BASE}/maps/dir/{formated_path}"
    browser.send_request("GET", direction_url)
    direction_url_preview = f"{URL_BASE}{browser.get_soup().find("link")["href"]}"
    response = browser.send_request("GET", direction_url_preview)
    json_str = response.text.replace(")]}'", "").strip()
    padrao = r'\[\d+,\s*"([^"]+)",\s*\[\d+,\s*"([\d,]+\s*km)",\s*\d+\],\s*\[\d+,\s*"([\d\s\w]+)"\]'
    match = re.search(padrao, json_str)
    if match:
        distance_total = match.group(2)
        time_total = match.group(3)
        return {
            "url": requests.utils.requote_uri(direction_url),
            "distance": distance_total,
            "time": time_total
        }

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
            hours = int(parts[i - 1])
        elif parts[i] == 'min':
            minutes = int(parts[i - 1])

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


def calculate_distance(lat1, lon1, lat2, lon2):
    """Retorna a distância em metros entre dois pontos."""
    return geodesic((lat1, lon1), (lat2, lon2)).meters
