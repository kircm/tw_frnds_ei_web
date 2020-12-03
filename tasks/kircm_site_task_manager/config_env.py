import environ
import os

root = environ.Path(__file__) - 2  # get root of the project
env = environ.Env()
environ.Env.read_env(os.path.join(root(), '.env'))  # reading .env file

DEBUG = env.bool('DEBUG')

MYSQL_DB_HOST = env('MYSQL_DB_HOST')
MYSQL_DB_PASSWORD = env('MYSQL_DB_PASSWORD')

TW_FRNDS_EI_APP_KEY = env('TW_FRNDS_EI_APP_KEY')
TW_FRNDS_EI_APP_SECRET = env('TW_FRNDS_EI_APP_SECRET')

ROTATING_LOG = env('ROTATING_LOG')
