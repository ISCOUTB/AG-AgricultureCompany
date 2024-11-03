import os

APP_ENV = os.getenv('APP_ENV', 'development')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME', 'adm')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '12345')
DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'agriculture')
TEST_DATABASE_NAME = os.getenv('DATABASE_NAME', 'agriculture_test')
