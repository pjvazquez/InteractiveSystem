# coding=utf-8

import cv2
import json
import numpy as np
from datetime import datetime
from functools import wraps
from __init__ import VERSION
from utils import get_logger


logger = get_logger(__name__)


# retrieve and parse configuration
with open("../Config/application.conf", "r") as confFile:
    conf = json.loads(confFile.read())

happiness_threshold = conf('happiness_threshold')

class InteractiveSystem():
