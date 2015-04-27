import os


def log_dir():
    return os.path.dirname(os.path.abspath(__file__)) + '/..'


def db_url():
    return 'mongodb://localhost:27017/'
