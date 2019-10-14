# coding=utf-8

import json
import math
import traceback
import imutils
import StateManager
import time
import utils
import cv2
from __init__ import VERSION
from utils import get_logger

logger = get_logger(__name__)

# retrieve and parse configuration
with open("./Config/application.conf", "r") as confFile:
    conf = json.load(confFile)

imagePath = conf['image_path']

class GetImages:
    def __init__(self, statesName = 'states'):
        self.statesName = statesName

    def getImageConf(self):
        with open("./Config/Images.conf") as imageFile:
            imageData = json.loads(imageFile.read())
        return imageData

    def generateImageDict(self):
        # loads into a dictionary all images we are going to use
        # each state has its own images
        bg_images = {}
        imageData = self.getImageConf()
        for i, state in enumerate(StateManager.states2):
            bg = cv2.imread(imagePath + imageData[state][0]['imagename'])
            bg = cv2.resize(bg, (3840,2160))
            bg_images[state]=bg
        return bg_images