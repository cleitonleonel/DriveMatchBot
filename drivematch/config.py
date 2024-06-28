import tomllib

with open('config.toml', 'rb') as f:
    config = tomllib.load(f)

API_ID = config['API']['ID']
API_HASH = config['API']['HASH']
BOT_TOKEN = config['API']['BOT_TOKEN']
ADMIN_IDS = config['ADMIN']['IDS']
COMPANY_NAME = config['COMPANY']['NAME']
