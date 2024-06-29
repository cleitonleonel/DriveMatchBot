import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import toml


def load_config(file_path):
    if sys.version_info >= (3, 11):
        with open(file_path, 'rb') as f:
            return tomllib.load(f)
    with open(file_path, 'r') as f:
        return toml.load(f)


config = load_config('config.toml')

API_ID = config['API']['ID']
API_HASH = config['API']['HASH']
BOT_TOKEN = config['API']['BOT_TOKEN']
ADMIN_IDS = config['ADMIN']['IDS']
APP_NAME = config['APPLICATION']['APP_NAME']
APP_AUTHOR = config['APPLICATION']['APP_AUTHOR']
APP_VERSION = config['APPLICATION']['APP_VERSION']
DEVICE_MODEL = config['APPLICATION']['DEVICE_MODEL']
SYSTEM_VERSION = config['APPLICATION']['SYSTEM_VERSION']
