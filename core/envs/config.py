import os
from pathlib import Path
from environs import Env

# todo: With environs take .env file datas
env = Env()
# Open .env file in core/envs folder
if os.path.exists('core/envs/.env'):
    env.read_env(os.path.join(
        Path(__file__).resolve().parent.parent, 'envs', '.env'))
else:
    print('.env file not found!')
    print('Copy .env.example  and fill it with your data!')
    exit(1)


# todo: .env file datas
HEMIS_API_TOKEN = env.str('HEMIS_API_TOKEN')
HEMIS_UNIVERSITY_API_BASE_URL = env.str('HEMIS_UNIVERSITY_API_BASE_URL')

SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env.bool('DEBUG')
BASE_URL = env.str('BASE_URL')

# PostgreSQL
DB_NAME = env.str('DATABASE_NAME')
DB_USER = env.str('DATABASE_USERNAME')
DB_PASS = env.str('DATABASE_PASSWORD')
DB_HOST = env.str('DATABASE_HOST')
DB_PORT = env.str('DATABASE_PORT')
