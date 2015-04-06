from util.env import log_dir
import logging


class MyFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return logging.Formatter.formatTime(self, record, datefmt).replace(',', '.')


def get(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    formatter = MyFormatter('%(asctime)s:%(levelname)s:%(message)s')
    ch = logging.FileHandler(log_dir() + '/news_diff.log')
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log