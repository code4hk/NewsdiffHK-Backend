import os


def log_dir():
    openshift_log_dir = os.environ.get('OPENSHIFT_LOG_DIR')
    if openshift_log_dir:
        return openshift_log_dir
    else:
        return os.path.dirname(os.path.abspath(__file__)) + '/..'


def db_url():
    openshift_db_url = os.environ.get('OPENSHIFT_MONGODB_DB_URL')
    if openshift_db_url:
        return openshift_db_url
    else:
        return 'mongodb://localhost:27017/'
