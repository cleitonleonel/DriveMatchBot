import tomllib

with open('config.toml', 'rb') as f:
    config = tomllib.load(f)

API_ID = config['API']['ID']
API_HASH = config['API']['HASH']
BOT_TOKEN = config['API']['BOT_TOKEN']
ADMIN_IDS = config['ADMIN']['IDS']
APP_NAME = config['APPLICATION']['APP_NAME']
APP_AUTHOR = config['APPLICATION']['APP_AUTHOR']
APP_VERSION = config['APPLICATION']['APP_VERSION']
DEVICE_MODEL = config['APPLICATION']['DEVICE_MODEL']
SYSTEM_VERSION = config['APPLICATION']['SYSTEM_VERSION']
