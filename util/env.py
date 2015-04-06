import os


def data_dir():
    openshift_data_dir = os.environ.get('OPENSHIFT_DATA_DIR')
    if openshift_data_dir is None:
        return os.path.dirname(os.path.abspath(__file__))+'/..'
    else:
        return openshift_data_dir


def log_dir():
    openshift_log_dir = os.environ.get('OPENSHIFT_LOG_DIR')
    if openshift_log_dir is None:
        return os.path.dirname(os.path.abspath(__file__))+'/..'
    else:
        return openshift_log_dir