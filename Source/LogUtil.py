# coding=utf-8

import logging
import sys
from logging.handlers import RotatingFileHandler


from __init__ import DEFAULT_LOGGING_LEVEL


def get_logger(name, level=DEFAULT_LOGGING_LEVEL):

    from datetime import datetime

    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch0 = logging.StreamHandler(sys.stdout)
    ch0.setLevel(level)
    ch1 = RotatingFileHandler('./Logs/interactiveSystem.log', maxBytes=5000000, backupCount=10)
    ch1.setLevel(level)
    # TODO: use a rotatingFileHandler in the deployment mode

    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    ch0.setFormatter(formatter)
    ch1.setFormatter(formatter)

    logger.addHandler(ch0)
    logger.addHandler(ch1)

    return logger

